# Client — PySide6 图形客户端

托盘常驻采集进程：配置界面、隐私开关、开机自启，后台采集并推送到服务端。

## 功能清单

重写客户端时按下表逐项对齐。标「行为契约」的是容易在重写中丢掉、但用户已在依赖的细节。

### 一、进程与生命周期

| 功能 | 说明 |
|------|------|
| 托盘常驻 | 关闭主窗口只 `hide()`，进程不退（`setQuitOnLastWindowClosed(False)`） |
| 托盘左键 | 单击 / 双击 / 中键 → 显示主窗口 |
| 托盘右键 | 菜单：打开设置、退出（macOS 因模板图标特性由 mouse-press 弹菜单） |
| macOS 隐藏 Dock | 启动时用 `setActivationPolicy(1)` 变成纯菜单栏应用 |
| 首启判断 | `client.json` 不存在或 `setup_completed=false` → 弹初始化向导 |
| 启动形态 | `ui.start_minimized` 为 true 时只留托盘，不弹主窗 |
| 退出 | 停采集线程 → `thread.wait(5000)` → 释放 API 线程 → `app.quit()` |

### 二、采集与上报

| 能力 | 数据 | 平台实现 |
|------|------|----------|
| 心跳 | `ts` / `client{id,platform,version}` / `privacy` 快照 | 全平台，`httpx.post` 同步 |
| 系统负载 | CPU%、内存%、1/5/15 分钟 load avg | psutil（Windows 无 load avg 时给空数组） |
| 音乐 | 状态 / 曲名 / 歌手 / 专辑 / 播放器 / 进度 / 时长 / 封面 | macOS 走 `osascript`（Apple Music + Spotify 两套脚本，多候选取 playing 优先）；Windows 走 WinRT GSMTC；Linux 走 MPRIS over D-Bus |
| 封面 | 从播放器取原始图 → 缩成 200px 方图 JPEG(q80) → `PUT /api/v1/cover/{client_id}` → 回填 `cover_url` | 全平台 |
| 进程列表 | 白名单正则过滤 + 排除表 + 按名称聚合计数 | psutil，三平台共用 |
| 进程采集模式 | `process_collect_all=true` 时收「看起来是用户应用」的进程（排除系统路径），否则只认白名单 | 三平台共用 |
| 截图 | 全屏抓取 → 高斯模糊 → 缩放 → WebP(q75) → `PUT` 上传 | mss + Pillow |
| 失败退避 | 心跳失败按 `retry_backoff_seconds` 表递增（默认 0/5/15/60/300 秒），成功立刻回到正常间隔 | 查表，非 if/elif |

**行为契约**：截图必须先在本机完成模糊与 WebP 压缩再上传，原始图不出本机；`privacy` 关闭的能力不得采集、不得进 payload、不得留字段。

### 三、隐私

| 层级 | 开关 | 效果 |
|------|------|------|
| 总闸 | `push.enabled` | 关闭则采集定时器停摆（进程仍常驻托盘） |
| 细粒度 | `collect_screenshot` / `collect_media` / `collect_processes` / `collect_system_load` | 在适配器入口短路，返回 None / 空列表 |

`privacy` 当作 payload 的一部分上报给服务端，前端据此显示采集范围。

### 四、界面

主窗口宽 960×640，左侧导航栏 + 右侧内容栈，另加菜单栏「语言」。五个页面：

| 页面 | 功能 |
|------|------|
| 设置 | 服务端地址、API 密钥、GitHub PAT、GitHub 用户名、推送开关、间隔（5–3600 秒）、四个隐私开关、截图模糊半径（0–100）/ 缩放（0.05–1.0）/ 画质（1–100）、开机自启、启动后最小化、站点文案（见第五节）、保存 / 关闭 / 上传网页背景 |
| 诊断 | 现场采集的音乐卡片（含封面缩略图）、进程列表、显示列表（可增删，右键菜单）、系统负载、最近 20 条推送结果；页面可见时每 5 秒自动刷新，隐藏即停 |
| 日记 | 列表 + 编辑区（标题 / 心情 / 标签 / Markdown 正文）+ 实时预览，新建 / 保存 / 删除 |
| 友链 | 列表 + 表单（名称 / 链接 / 头像 / 描述 / 排序），新建 / 保存 / 删除 |
| 留言 | 上半留言列表（显示 作者·IP·属地·正文·回复条数，tooltip 展开回复），下半封禁 IP 列表；支持回复、删除留言、封禁 IP / 解封、刷新；每 8 秒自动轮询 |

另有两个弹窗：

| 弹窗 | 功能 |
|------|------|
| 初始化向导 | 三页：依赖工具（检测 nowplaying-cli / Homebrew，一键 brew 安装）、系统权限（屏幕录制、自动化，一键跳系统设置 + 重新检测）、服务端配置（地址 + API 密钥） |
| 回复对话框 | 显示原留言与已有回复，输入回复（上限 500 字，空内容禁用发送） |

**行为契约**：界面只发信号，HTTP 全在独立线程；语言切换后所有面板文案立刻刷新（`retranslate`）。

### 五、站点内容管理

设置页里改的站点文案保存后立即推送到服务端，前端页面据此渲染：

| 字段 | 说明 |
|------|------|
| `title` / `tagline` | 网页标题与副标题 |
| `process_title` | 软件标签云区块标题 |
| `tags_title` / `tags` | 标签卡片标题与标签数组（逗号分隔输入） |
| `show_heatmap` | 是否显示 GitHub 贡献热力图 |
| `show_icp` / `icp_text` / `icp_keyword` | 备案号显示开关、文字、关键字 |
| `github_owner` / `github_repo` | 前端「查看源码」指向的仓库 |

另外两个内容操作：上传网页背景图（本地压到长边 1600px、JPEG q78 并在 2.2 MB 内，再 `PUT /api/v1/background`）；推送 GitHub PAT（保存设置时 `POST /api/v1/github/token`，失败只记日志）。

### 六、通知

新留言到达（8 秒轮询发现未见过的新 id）时，弹系统通知：macOS `osascript display notification`、Windows PowerShell Toast、Linux `notify-send`。

### 七、国际化

中文 / 英文两套完整字符串表，覆盖主窗口、菜单、托盘、向导、全部面板文案；语言存在 `ui.language`，切换后即时生效并持久化。

### 八、开机自启

| 平台 | 机制 |
|------|------|
| macOS | LaunchAgent `~/Library/LaunchAgents/com.heartbeat.client.plist` + `launchctl bootstrap/bootout` |
| Windows | 注册表 `HKCU\...\CurrentVersion\Run` |
| Linux | `~/.config/autostart/heartbeat-client.desktop` |

打包后必须注册产物路径，不能注册 `python main.py`。

### 九、客户端调用的服务端接口

| 方法 | 路径 | 触发时机 |
|------|------|----------|
| POST | `/api/v1/heartbeat` | 每 `push.interval_seconds` 一次，带 `X-API-Key`、`X-Client-Version` |
| PUT | `/api/v1/screenshot/{client_id}` | 心跳响应带 `screenshot_upload_url` 时 |
| PUT | `/api/v1/cover/{client_id}` | 有封面图时 |
| GET/POST/PATCH/DELETE | `/api/v1/diaries[/{id}]` | 日记页 |
| GET/POST/PATCH/DELETE | `/api/v1/friends[/{id}]` | 友链页 |
| GET | `/api/v1/messages/admin` | 留言页，8 秒轮询 |
| POST | `/api/v1/messages/{id}/replies` | 回复留言 |
| DELETE | `/api/v1/messages/{id}` | 删除留言（连带删回复） |
| GET/POST/DELETE | `/api/v1/messages/bans[/{id}]` | 封禁管理 |
| POST | `/api/v1/github/token` | 保存设置后推 PAT |
| PUT | `/api/v1/site` | 保存设置后推站点文案 |
| PUT | `/api/v1/background` | 手动上传背景图 |

客户端**不调用** `/status`、`/stream`、`/github`、`/site`、`/background`(GET)、`/messages`(GET) —— 那些是 Web 前端的读接口。

### 十、已知缺口

- `push.max_queue_size` 只在配置模型里存在，**没有实现**：断网期间的心跳不会缓冲补传，失败只是退避重试当前这一条。
- 客户端日志只走 `logging.basicConfig`（stderr），没有落盘。打包成 `.app` 后从 Finder 启动看不到任何日志，排障困难。
- 诊断面板的「显示列表」与设置页的「进程白名单」是同一份数据（`process_whitelist`），改一处两处都变。

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
  "process_collect_all": true,
  "autostart": { "enabled": false },
  "ui": { "start_minimized": true, "language": "zh-CN" },
  "site": {
    "title": "HeartBeat",
    "tagline": "个人主页与实时状态",
    "process_title": "TA的电脑上正在玩",
    "show_heatmap": true,
    "tags_title": "标签",
    "tags": [],
    "show_icp": false,
    "icp_text": "萌ICP备20263011号",
    "icp_keyword": "20263011",
    "github_owner": "SoraSushi776",
    "github_repo": "HeartBeat"
  }
}
```

`client.secrets.json` 存三个键，均 chmod 0600：`api_key`、`github_token`、`github_login`。

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
