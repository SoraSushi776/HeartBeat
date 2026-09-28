# HeartBeat 客户端技术调研笔记

临时研究笔记。覆盖 PySide6 应用骨架、后台采集解耦、配置持久化、隐私开关、打包。
结论见文末「选型结论」。

---

## 1. PySide6 应用骨架

### 1.1 QApplication + QSystemTrayIcon

关键 API（Qt for Python 官方）：

- `QSystemTrayIcon()` / `setIcon(QIcon)` / `setToolTip(str)` / `setContextMenu(QMenu)` / `setVisible(True)`
- `activated(reason)` 信号，`reason` 为 `ActivationReason.Unknown / Context / DoubleClick / Trigger / MiddleClick`
- `showMessage(title, msg, icon, msecs)` 气泡通知；`supportsMessages()` 可用性探测
- 静态 `isSystemTrayAvailable()` 探测托盘是否存在；托盘后出现时 Qt 会自动补上可见图标

跨平台注意事项：

| 平台 | 行为 |
|------|------|
| Windows | 托盘图标尺寸 16x16，气泡超时 `msecs` 常被系统忽略（应用有焦点时） |
| X11/Linux | 偏好尺寸 22x22；无托盘桌面（部分 GNOME）`isSystemTrayAvailable()` 为 False |
| macOS | 菜单栏应用。`DoubleClick` 仅在**未设置** contextMenu 时发出（菜单在 mouse-press 就弹出） |

macOS 菜单栏适配要点：

1. `app.setQuitOnLastWindowClosed(False)` 必须设置，否则关掉配置窗口整个进程退出。
2. 图标需用 **template image**：`QIcon` 上调用 `setIsMask(True)`，系统会按菜单栏明暗自动反色。Sonoma 起菜单栏会随壁纸/辅助功能切换黑/白/半透明，普通彩色图标会脏、会糊。
3. 菜单用 `QMenu` + `QAction`（PySide6 中 `QAction` 在 `QtGui`），`tray.setContextMenu(menu)`。菜单所有权归调用方，需给 `QMenu` 指定 parent 防泄漏。

最小骨架：

```python
app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
app.setOrganizationName("HeartBeat")
app.setApplicationName("HeartBeatClient")

icon = QIcon("icon.png")
icon.setIsMask(True)

tray = QSystemTrayIcon(icon)
menu = QMenu()
menu.addAction("Open Dashboard", show_window)
menu.addAction("Quit", app.quit)
tray.setContextMenu(menu)
tray.show()
app.exec()
```

### 1.2 最小化到托盘

- 关窗口不退出：`app.setQuitOnLastWindowClosed(False)` + 重写主窗口 `closeEvent` 改为 `hide()`（或 `QSystemTrayIcon` 菜单里给 Show/Hide）。
- 首次启动是否弹窗：配置项 `ui.start_minimized`，默认 true（纯后台采集场景）。
- macOS 已是菜单栏常驻，"最小化到托盘"退化为"隐藏主窗口"。

### 1.3 开机自启

业务代码禁止 `sys.platform` 分支 → 各平台自启写成独立适配器（`client/autostart/`），暴露统一接口 `AutostartProvider.enable() / disable() / is_enabled()`。

| 平台 | 机制 | 路径 / 键 | 实现 |
|------|------|-----------|------|
| Windows | 注册表 Run | `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`，值名 `HeartBeat`，数据为可执行文件完整路径 | `winreg.SetValueEx` / `DeleteValue`（无需管理员，HKCU 即可） |
| macOS | LaunchAgent | `~/Library/LaunchAgents/com.heartbeat.client.plist` | 写 plist（`Label`/`ProgramArguments`/`RunAtLoad`/`KeepAlive`），`launchctl bootstrap gui/$(id -u) <plist>` 加载，`launchctl bootout` 卸载 |
| Linux | XDG Autostart | `~/.config/autostart/heartbeat-client.desktop` | 写 Desktop Entry（`Type=Application`/`Exec=`/`X-GNOME-Autostart-enabled=true`）。规范见 freedesktop Autostart Spec：同名文件用户目录优先；`Hidden=true` 表示禁用；`OnlyShowIn`/`NotShowIn` 可限定桌面环境 |

Linux 取舍说明：systemd user unit 也可，但普通 GUI 应用走 XDG Autostart 更符合桌面惯例，且 GNOME/KDE/XFCE 都认。仅在需要 KeepAlive 级守护时才考虑 systemd。

打包后自启必须指向**产物路径**（`.app` / exe / AppImage），不是 `python main.py`。`AutostartProvider` 需接受可执行路径参数，打包脚本/安装脚本负责注入。

### 1.4 界面：代码拼 vs .ui vs Qt Design Studio

| 方案 | 适用 | 代价 |
|------|------|------|
| 代码拼装 | 动态表单、配置项由数据驱动 | 大界面啰嗦 |
| `.ui` + `pyside6-uic` 编译成 Python | 固定布局、多人协作 | 每次改 ui 要重新 `pyside6-uic xxx.ui -o ui_xxx.py` |
| `.ui` + `QUiLoader` 运行时加载 | 原型 | 自定义 Python 控件/类型不友好（connect 用字符串签名）；打包要带 .ui |
| Qt Design Studio | 复杂 QML / 设计师协作 | 引入 QML 栈，对本项目过重 |

推荐：**代码拼装为主**。HeartBeat 配置面板是开关 + 输入框 + 列表驱动，代码拼更直接，也符合 AGENTS「可调参数一律进配置层，禁止散落在控件私有字段」的要求。若后续出现复杂固定布局（快照弹窗），再引入 `.ui` + `pyside6-uic`（编译进包，不运行时加载）。

`pyside6-uic` 生成物、`.qrc`/`pyside6-rcc` 生成物不进业务逻辑，只被 UI 层 import。

---

## 2. 后台采集与 UI 解耦

### 2.1 三种模式对比

| 模式 | 适合 | 不适合 |
|------|------|--------|
| `QThread` + `moveToThread(Worker)` | 长驻采集循环（截图、轮询） | 一次性小任务 |
| `QThreadPool` + `QRunnable` | 短平快并行任务（批量上传、缩略图） | 需要事件循环 / 长连接 |
| asyncio + `qasync` / `PySide6.QtAsyncio` | 已有 asyncio 生态（httpx/aiohttp 推送） | 与 Qt 信号槽混用要小心事件循环归属 |

`PySide6.QtAsyncio`（6.6.2+，官方第一个纯 Python 模块）用 Qt 事件循环替换 asyncio 默认 loop，可 `import PySide6.QtAsyncio; PySide6.QtAsyncio.run(main())` 混用协程和 Qt。第三方 `qasync` 做的事类似但非官方。

推荐给 HeartBeat：

- **采集线程**：`QThread` + `moveToThread` 的 `Worker(QObject)`。截图/媒体/进程/系统负载各自 Worker，或一个 Collector Worker 内部分适配器调用。
- **推送**：同一 Worker 内同步 `requests`/`httpx` 阻塞调用即可（已在工作线程）；若想用 async 客户端，再引入 QtAsyncio，但**首版不引入**，保持依赖面小。
- **UI**：只订阅信号，不做 IO。配置读写、白名单过滤等纯内存操作可在 UI 线程。

标准 `moveToThread` 模式（推荐写法，勿子类化 `QThread`）：

```python
class CollectorWorker(QObject):
    snapshot_ready = Signal(dict)
    push_failed = Signal(str, int)

    @Slot()
    def run(self) -> None:
        while not self._stopped:
            data = self.collect()
            self.snapshot_ready.emit(data)
            ...
        self.finished.emit()

    finished = Signal()

thread = QThread()
worker = CollectorWorker()
worker.moveToThread(thread)
thread.started.connect(worker.run)
worker.finished.connect(thread.quit)
worker.snapshot_ready.connect(ui.on_snapshot)   # 自动 QueuedConnection
thread.start()
```

要点：

- `Signal` 必须定义在**类**上，不能定义在 `__init__` 实例上。
- Worker **不要** setParent 到 UI 对象（否则不能 moveToThread）。
- 跨线程 connect 默认 `AutoConnection`，跨线程自动变成 `QueuedConnection`，payload 需是可拷贝的 Qt 元类型（Python `dict`/`str`/`int` 在 PySide6 可直接跨线程传）。
- 退出：`finished → thread.quit`，再 `thread.wait()`；勿在工作线程直接碰控件。
- 勿在 UI 线程做阻塞 IO（AGENTS 明令）。

### 2.2 定时采集与推送重试

`QTimer` 挂在 Worker 所属线程（`QTimer(worker)` + `moveToThread` 后 start）或主线程发 `request_collect` 信号到 Worker。

推荐结构：

```python
class PushScheduler(QObject):
    push_requested = Signal(dict)
    backoff_seconds = [0, 5, 15, 60, 300]  # 查表，不写 if-elif

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._attempt = 0

    def start(self, interval_ms: int) -> None:
        self._timer.start(interval_ms)

    @Slot()
    def _on_tick(self) -> None:
        self.push_requested.emit(self._payload())

    @Slot()
    def on_push_ok(self) -> None:
        self._attempt = 0

    @Slot(str)
    def on_push_fail(self, reason: str) -> None:
        delay = self.backoff_seconds[min(self._attempt, len(self.backoff_seconds) - 1)]
        self._attempt += 1
        self._timer.start(delay * 1000)
```

- 采集周期、重试表、推送开关全部走配置，不硬编码。
- 失败退避用查表/策略对象，避免 `if/elif` 链（AGENTS 禁）。
- 离线队列：本地缓冲 N 条快照，恢复后批量补传；超出丢最旧。

---

## 3. 配置持久化

### 3.1 QSettings 跨平台行为

`QSettings.NativeFormat` 默认落点：

| 平台 | 位置 |
|------|------|
| Windows | 注册表 `HKCU\Software\<Org>\<App>` |
| macOS / iOS | `$HOME/Library/Preferences/com.<Org>.<App>.plist`（CFPreferences）。`organizationDomain` 优先于 `organizationName` 作为反向域名 |
| Unix | INI 文本文件（路径由 `QSettings::setPath` / XDG 决定，默认 `~/.config/<Org>/<App>.conf`） |

其他要点：

- `IniFormat` 可强制三平台统一 INI，但**数值会读回 QString**，需自己 `toInt()`。
- key 大小写：Windows 注册表/INI 不敏感，Unix 敏感 → 统一小写 key，避免大小写冲突。
- `/` 作层级分隔符，key 里不要写 `\`。
- fallback 机制：User/App → User/Org → System/App → System/Org，默认可读四层、只写第一层；`setFallbacksEnabled(False)` 关掉。
- `sync()` 显式刷盘；`status()` 可查 `AccessError` / `FormatError`。

### 3.2 QSettings vs JSON 文件 vs keyring

| 内容 | 推荐 |
|------|------|
| 非敏感偏好（开关、窗口、间隔、截图参数、白名单） | **JSON 配置文件** 或 QSettings 均可 |
| API 密钥等敏感 | **单独文件 + 权限 0600**，或 `keyring`（系统钥匙串） |
| 需用户手工改 / 版本管理 / 便携 | JSON 文件 |

推荐方案（贴合 AGENTS「敏感信息进本地配置，不进 Git」）：

- **主配置**：`~/.config/heartbeat/client.json`（macOS 可用 `~/Library/Application Support/HeartBeat/client.json`，由平台路径适配器给路径）。JSON，结构清晰，可 diff，可备份。
- **敏感配置**：`client.secrets.json`（或 QSettings 一个独立 scope），文件权限 0600，路径不进 Git，启动时读入内存，UI 上显示为掩码。
- 可选升级：API Key 走 `keyring` 包（macOS Keychain / Windows Credential Manager / Linux Secret Service），跨平台统一 `keyring.get_password/set_password`。首版用文件即可，接口留 `SecretStore` 协议便于替换。

不用 QSettings 作主配置的原因：跨平台落点不一致（注册表/plist/ini），调试和备份都麻烦；且 AGENTS 要求可配项集中、可审查，JSON 更直观。QSettings 可保留给纯 UI 状态（窗口几何）。

### 3.3 推荐配置结构

```json
{
  "server": {
    "base_url": "https://example.com",
    "timeout_seconds": 10
  },
  "push": {
    "enabled": true,
    "interval_seconds": 60,
    "retry_backoff_seconds": [0, 5, 15, 60, 300],
    "max_queue_size": 100
  },
  "privacy": {
    "collect_screenshot": true,
    "collect_media": true,
    "collect_processes": true,
    "collect_system_load": true
  },
  "screenshot": {
    "blur_radius": 12.0,
    "scale": 0.5,
    "format": "webp",
    "quality": 70
  },
  "process_whitelist": [
    "code",
    "chrome",
    "Safari"
  ],
  "autostart": {
    "enabled": false
  },
  "ui": {
    "start_minimized": true,
    "language": "zh-CN"
  }
}
```

`secrets.json`：

```json
{
  "api_key": "..."
}
```

配置层用 dataclass / pydantic 做 schema 校验，坏数据拒绝加载并回退默认值。

---

## 4. 隐私开关设计

两层：

1. **全局推送使能** `push.enabled`：总闸。关闭 → 推送调度器停表，不打包不上报。
2. **细粒度采集开关** `privacy.*`：截图 / 音乐 / 进程 / 系统负载。

采集层短路策略（在**采集层**生效，不是 UI 层）：

```python
class PrivacyGate:
    """按隐私开关短路采集能力"""

    def __init__(self, settings: PrivacySettings) -> None:
        self._settings = settings

    def allow(self, capability: Capability) -> bool:
        if not self._settings.global_enabled:
            return False
        return self._settings.enabled_for(capability)

class ScreenshotAdapter:
    def collect(self, gate: PrivacyGate) -> Screenshot | None:
        if not gate.allow(Capability.SCREENSHOT):
            return None
        ...
```

要点：

- 关闭的能力**不得采集、不得进入上报 payload**（AGENTS 明令）。短路在 adapter 入口，而不是采集完再丢字段。
- 能力用枚举 + 查表/多态，不用 `if/elif` 链。
- 开关变更发 `privacy_changed` 事件，采集线程与 UI 同步订阅；全局关闭时 Worker 进入空转或直接停 QTimer。
- 截图本地模糊 + WebP 压缩参数也在隐私相关配置里，半径/缩放可配，压缩后才离开本机。
- 进程白名单正则在采集层过滤，白名单变更同样事件通知。

---

## 5. 打包

### 5.1 PyInstaller vs Nuitka（2025–2026 现状）

| 维度 | PyInstaller | Nuitka |
|------|-------------|--------|
| 原理 | 打包解释器 + 字节码，运行时解释 | 编译成 C → 机器码 |
| 启动 | 较慢 | 快 |
| 体积 | 大（几十 MB 起） | 小 30–50% |
| 兼容性 | 极好 | 好，冷门库偶尔要配 |
| 反编译 | 易（pyinstxtractor） | 难 |
| 打包耗时 | 分钟级 | 需编译，更久 |
| Qt 插件处理 | hooks 自动（Qt6 现已支持；官方页面仍有历史警告文字） | `--plugin-enable=pyside6` 自动 |
| 杀软误报 | 常见 | 也常见，需签名 |

**Qt for Python 官方现状**（重要）：

- 官方推荐 `pyside6-deploy`（6.4+），它是 **Nuitka 的封装**，生成 `.exe` / `.bin` / `.app`。
- `pyside6-deploy` 自动生成 `pysidedeploy.spec`，可进版本库；自动识别 Qt 模块/插件、排除不需要的重模块（QtWebEngine 等）；macOS 可写 `NSCameraUsageDescription` 等权限串。
- 默认 Nuitka 4.1.1，可在 spec 里升级。
- 依赖工具：Windows `dumpbin`（MSVC）、Linux `readelf`、macOS `dyld_info`（macOS 12+）。

Nuitka 直接用：

```bash
pip install nuitka ordered-set zstandard
nuitka --standalone --onefile --windows-disable-console --enable-plugin=pyside6 main.py
```

资源文件必须显式声明：`--include-data-files=config.json=config.json`。Nuitka 编译后路径结构不同，代码里 `open("config.json")` 会炸 → 用 `__file__` 相对定位或打包清单。

### 5.2 PySide6 打包常见坑

1. **Qt 插件缺失**（platforms/qwindows/qcocoa 等）→ 运行即崩或白屏。Nuitka 用 `--plugin-enable=pyside6`；PyInstaller 靠 hooks，但要在干净 venv 里打。
2. **系统 Python 的 PySide6 抢优先级**：PyInstaller 可能无视 venv 里的版本，去用系统 site-packages → 打包前卸载系统 PySide6/shiboken6，或只用 `python -m pip` / `python -m PyInstaller`。
3. **图标/翻译/QML 插件被整包打入**（Nuitka QML 场景），体积爆炸 → `pysidedeploy.spec` 的 `excluded_qml_plugins`。纯 Widgets 项目无此问题。
4. **资源路径**：图标、模糊核配置等用 `Path(__file__).parent` 或 `sys._MEIPASS`（PyInstaller onefile 解压目录），不要 cwd 相对路径。
5. **杀软误报**：加代码签名；Nuitka 传 `--company-name` / `--product-name` 等元数据。
6. **macOS 权限**：截屏需 `NSScreenCaptureUsageDescription`（Screen Recording 在系统设置授权），配置进 `pysidedeploy.spec` 的 `macos.permissions`，否则 .app 静默无权限。
7. **onefile 启动慢**（解压到临时目录），tray 常驻应用无所谓；配置面板交互频繁时 standalone 更跟手。

### 5.3 单文件 vs 目录分发

| | onefile | standalone（目录） |
|--|---------|-------------------|
| 分发 | 一个文件，方便 | 文件夹 / .app / AppImage |
| 启动 | 每次解压，慢 | 快 |
| 更新 | 整个替换 | 可只换部分 |
| 适合 | 内部工具、简单交付 | 正式桌面发布、需要旁路资源 |

推荐 HeartBeat：

- **开发/CI**：standalone 目录（调试快、可看缺什么插件）。
- **用户分发**：
  - macOS：`.app` bundle（standalone + `pyside6-deploy` 产出 `.app`），便于 LaunchAgent/登录项。
  - Windows：目录分发 + 安装器（Inno Setup），或 onefile 给极简用户。
  - Linux：AppImage 或 standalone 目录 + `.desktop`。
- 打包脚本放 `scripts/`，产物不进 Git（AGENTS 打包节）。

---

## 选型结论

| 项 | 结论 |
|----|------|
| UI 框架 | PySide6（Qt 6）Widgets + QSystemTrayIcon；`setQuitOnLastWindowClosed(False)`；macOS 图标 `QIcon.setIsMask(True)` |
| UI 拼装 | **代码拼装**为主；固定复杂布局再引入 `pyside6-uic` 编译生成 |
| 后台采集 | **`QThread` + `moveToThread(Worker)`**，信号槽 `Auto/QueuedConnection` 跨线程；推送短任务可用 `QThreadPool`；首版不上 asyncio |
| 定时与重试 | `QTimer` + 退避查表；离线队列限长 |
| 配置 | **JSON 主配置**（平台路径适配器）+ **secrets 文件（0600）或 keyring**；QSettings 仅作 UI 状态备选 |
| 隐私 | 全局 `push.enabled` + `privacy.*` 细粒度；短路在采集 adapter 入口，关闭能力不进 payload |
| 自启 | 平台适配器：Win 注册表 Run / macOS LaunchAgent plist / Linux XDG `.desktop` |
| 打包 | **首选 `pyside6-deploy`（Nuitka 封装）**；开发 standalone，发布 macOS `.app` + Win 目录安装包 + Linux AppImage；脚本进 `scripts/` |

一句话：**PySide6 Widgets 托盘常驻 + Worker/QThread 采集 + JSON 配置（密钥分离）+ pyside6-deploy/Nuitka 打包**。

---

## 来源

- QSystemTrayIcon API — https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSystemTrayIcon.html
- System Tray & Mac Menu Bar Applications in PySide6 — https://www.pythonguis.com/tutorials/pyside6-system-tray-mac-menu-bar-applications/
- macOS Sonoma 托盘 template image（`setIsMask`）— https://www.volcengine.com/article/1186361
- Desktop Application Autostart Specification（XDG）— https://specifications.freedesktop.org/autostart/latest/
- QSettings Class（平台落点 / Format / fallback）— https://doc.qt.io/qt-6/qsettings.html
- Using .ui files with QUiLoader and pyside6-uic — https://doc.qt.io/qtforpython-6/tutorials/basictutorial/uifiles.html
- PySide6 QThread 推荐实现（moveToThread）— https://cloud.tencent.com/developer/article/2240935
- QtAsyncio 笔记（PySide6.6.2+）— https://blog.debao.me/2024/03/notes-on-qtasyncio-and-pyside6/
- Qt for Python & Nuitka — https://doc.qt.io/qtforpython-6/deployment/deployment-nuitka.html
- Qt for Python & PyInstaller — https://doc.qt.io/qtforpython-6/deployment/deployment-pyinstaller.html
- pyside6-deploy 部署工具 — https://doc.qt.io/qtforpython-6/deployment/deployment-pyside6-deploy.html
- Deployment 总览（推荐 pyside6-deploy）— https://doc.qt.io/qtforpython-6/deployment/index.html
- Nuitka vs PyInstaller 打包对比（含避坑）— https://blog.csdn.net/m0_61749394/article/details/162103964
- keyring（跨平台密钥）— https://pypi.org/project/keyring/ / https://keyring.readthedocs.io/en/stable/
