# Client — PySide6 图形客户端

托盘常驻采集进程：配置界面、隐私开关、开机自启，后台采集并推送到服务端。

## 选型

| 项 | 选择 |
|----|------|
| UI | PySide6（Qt 6）Widgets |
| 托盘 | `QSystemTrayIcon` |
| 采集线程 | `QThread` + `moveToThread(Worker)` |
| 定时 | `QTimer` + 退避查表 |
| 配置 | JSON 主配置 + 独立 secrets |
| UI 拼装 | 代码拼装为主 |
| 首版 async | 不引入 qasync / QtAsyncio |

## 目录

```text
client/
├── main.py            入口与 QApplication
├── tray.py            系统托盘
├── i18n.py            中英文字符串表与 Translator
├── markdown.py        Markdown 子集转 HTML
├── diagnostics.py     诊断快照模型与封面解码
├── api.py             日记与友链 HTTP 服务
├── setup.py           工具与系统权限检查
├── window/            主窗口与各功能面板
│   ├── main_window.py     宽窗口（导航 + 内容栈 + 语言菜单）
│   ├── settings_view.py   设置面板
│   ├── diagnostics_view.py 诊断面板
│   ├── diary_view.py      日记编辑面板
│   ├── friends_view.py    友链编辑面板
│   ├── setup_wizard.py    初始化向导
│   └── window_manager.py  窗口与 API 线程编排
├── worker/            采集与推送 Worker
├── config/            配置加载、校验、路径
├── autostart/         平台自启适配
└── privacy.py         隐私门转发
```

主窗口约 960x640，左侧导航（设置 / 诊断 / 日记 / 友链）+ 右侧内容栈。语言菜单切换 `ui.language` 后调用各面板 `retranslate` 刷新文案。

初始化向导在首启或 `setup_completed=false` 时弹出，分工具、权限、服务端三页，完成后写入 `setup_completed=true`。

诊断面板从 adapters 现场采集（走 CollectorWorker 的 `collect_diagnostics`，隐私门短路），显示音乐封面与元数据、进程标签、系统负载、最近推送结果。

日记与友链面板走 `/api/v1/diaries` 与 `/api/v1/friends`，由 `ApiWorker` 在独立线程执行 HTTP，UI 只发信号。

## 应用骨架

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

### 托盘要点

| 平台 | 行为 |
|------|------|
| Windows | 图标 16x16；气泡超时可能被系统忽略 |
| Linux | 偏好 22x22；部分 GNOME 无托盘，`isSystemTrayAvailable()` 为 False |
| macOS | 菜单栏应用；图标必须 `QIcon.setIsMask(True)` 做 template image |

macOS 上设置了 contextMenu 时 `DoubleClick` 不会发出，菜单在 mouse-press 就弹出。关窗口改为 `hide()`，不退出进程。`ui.start_minimized` 控制首启是否直接后台。

## 采集与推送

标准 `moveToThread` 模式，不要子类化 `QThread`：

```python
class CollectorWorker(QObject):
    snapshot_ready = Signal(dict)
    push_failed = Signal(str, int)
    finished = Signal()

    @Slot()
    def run(self) -> None: ...

thread = QThread()
worker = CollectorWorker()
worker.moveToThread(thread)
thread.started.connect(worker.run)
worker.finished.connect(thread.quit)
worker.snapshot_ready.connect(ui.on_snapshot)
thread.start()
```

要点：

- `Signal` 定义在类上，不能放在 `__init__`
- Worker 不要 setParent 到 UI 对象
- 跨线程 `AutoConnection` 自动变 `QueuedConnection`
- 退出走 `finished → thread.quit`，再 `thread.wait()`
- UI 线程禁止阻塞 IO

推送在同一 Worker 内用同步 `httpx` 即可。失败退避用查表，不用 `if/elif`：

```python
backoff_seconds = [0, 5, 15, 60, 300]
delay = backoff_seconds[min(attempt, len(backoff_seconds) - 1)]
```

可选离线队列：本地缓冲 N 条，恢复后补传，超出丢最旧。采集周期、重试表、队列长度全走配置。

## 配置

### 文件

| 文件 | 内容 | 权限 |
|------|------|------|
| `client.json` | 服务端、推送、隐私、截图、白名单、自启、UI | 普通 |
| `client.secrets.json` | `api_key` | 0600 |

路径由平台路径适配器给出：

- Linux：`~/.config/heartbeat/`
- macOS：`~/Library/Application Support/HeartBeat/`
- Windows：`%APPDATA%/HeartBeat/`

QSettings 跨平台落点不一致（注册表/plist/ini），只作窗口几何等 UI 状态备选，不作主配置。后续可升级 `keyring` 存密钥，接口留 `SecretStore` 协议。

### 结构

```json
{
  "client_id": "abc123def456",
  "setup_completed": true,
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
    "blur_radius": 10.0,
    "scale": 0.25,
    "quality": 75
  },
  "process_whitelist": ["Code", "Safari"],
  "autostart": { "enabled": false },
  "ui": { "start_minimized": true, "language": "zh-CN" }
}
```

配置用 dataclass 或 Pydantic 校验，坏数据拒绝加载并回退默认值。可配项禁止散落在控件私有字段。

## 隐私

两层：

1. `push.enabled` 总闸，关闭则推送调度停表
2. `privacy.*` 细粒度：截图、音乐、进程、系统负载

短路在采集适配器入口，关闭能力不得采集、不得进 payload。开关变更发事件，采集线程与 UI 同步订阅。

## 开机自启

`client/autostart/` 提供统一接口：

```python
class AutostartProvider(Protocol):
    def enable(self) -> None: ...
    def disable(self) -> None: ...
    def is_enabled(self) -> bool: ...
```

| 平台 | 机制 | 路径或键 |
|------|------|----------|
| Windows | 注册表 Run | `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` |
| macOS | LaunchAgent | `~/Library/LaunchAgents/com.heartbeat.client.plist` |
| Linux | XDG Autostart | `~/.config/autostart/heartbeat-client.desktop` |

macOS 用 `launchctl bootstrap` / `bootout` 加载卸载。Linux 同名文件用户目录优先，`Hidden=true` 表示禁用。打包后自启必须指向产物路径，由安装脚本注入，不是 `python main.py`。

## 界面

代码拼装为主，配置面板是开关、输入框、列表驱动。若出现复杂固定布局，再引入 `pyside6-uic` 编译生成，不要运行时 `QUiLoader`。

界面只做展示与发信号，采集与推送在 Worker。控件引用靠脚本字段挂接，禁止按名字搜子节点。

## 坑

1. `setQuitOnLastWindowClosed(False)` 必须设，否则关窗即退
2. macOS 菜单栏图标不 `setIsMask(True)` 会在明暗切换时脏污
3. macOS 有 contextMenu 时收不到 DoubleClick
4. Signal 不能定义在实例上
5. Worker 不能 setParent 后再 moveToThread
6. 资源路径用 `Path(__file__).parent`，不要 cwd 相对路径
