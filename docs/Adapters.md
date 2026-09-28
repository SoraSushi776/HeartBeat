# Adapters — 跨平台采集适配

负责截图、媒体播放、进程列表、系统负载的采集。平台差异全部封在本模块，业务代码不得出现 `sys.platform` 分支。

## 职责

- 各平台底层 API 适配，统一输出可 JSON 序列化结构
- 隐私开关在采集入口短路，关闭的能力不采集、不进 payload
- 截图本地完成高斯模糊与 WebP 压缩后才离开本机
- 进程按正则白名单过滤

## 目录

```text
adapters/
├── base.py            协议与统一数据结构
├── privacy.py         隐私门
├── screenshot/        截图、模糊、编码
├── media/             正在播放
│   ├── windows.py
│   ├── macos.py
│   └── linux.py
├── processes/         进程白名单
└── system/            CPU、内存、负载
```

## 统一数据结构

```python
class MediaInfo(TypedDict):
    state: str
    title: str | None
    artist: str | None
    album: str | None
    app: str | None
    cover: bytes | str | None
    position_ms: int | None
    duration_ms: int | None

class ProcessInfo(TypedDict):
    name: str
    count: int

class ScreenshotResult(TypedDict):
    webp: bytes
    width: int
    height: int
```

各适配器实现同名协议方法，由工厂按平台选择实现。能力用枚举加查表分发，禁止 `if/elif` 链。

## 隐私门

```python
class Capability(Enum):
    SCREENSHOT = "screenshot"
    MEDIA = "media"
    PROCESSES = "processes"
    SYSTEM = "system"

class PrivacyGate:
    def allow(self, capability: Capability) -> bool: ...
```

每个适配器 `collect()` 入口先问 `PrivacyGate`，不允许则直接返回 `None`，不得先采再丢。全局推送使能关闭时，采集调度整体停表。

## 截图

### 选型

| 库 | 结论 |
|----|------|
| **mss 10.x** | 主方案。零依赖、快、线程安全、多显示器模型清晰 |
| Pillow ImageGrab | 备选。仅当需要单窗口 `window=` 截取且帧率要求低 |

### 链路

```text
mss 抓帧 → Image.frombytes → resize 降采样 → GaussianBlur → save WEBP
```

```python
from mss import MSS
from PIL import Image, ImageFilter

with MSS() as sct:
    shot = sct.grab(sct.monitors[1])
    img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

img = img.resize((w // 4, h // 4), Image.Resampling.LANCZOS)
img = img.filter(ImageFilter.GaussianBlur(radius=10))
img.save(buf, format="WEBP", quality=75, method=4)
```

### 参数（可配）

| 项 | 默认 | 说明 |
|----|------|------|
| `blur_radius` | 10 | 高斯核标准差 |
| `scale` | 0.25 | 边长缩放比，先降采样再模糊更快 |
| `quality` | 75 | WebP 有损质量，已强模糊的图 70–75 足够 |
| `method` | 4 | WebP 压缩力度 0–6 |

### 注意

- 先降采样再模糊，等效半径更大、速度快一个数量级
- 全程内存处理，不落盘明文截图
- 模糊与编码是 CPU 密集，放工作线程，禁止阻塞 UI
- mss 现行 API 是 `from mss import MSS`，不是 `mss.mss()`
- 与 pyautogui 等共存时必须先 `import mss`，否则 Windows DPI 错乱
- Pillow ImageGrab 在 macOS Retina 默认 2x，需 `scale_down=True`（Pillow 12.3+）才退回 1x
- Linux X11 失败时 ImageGrab 会回落 `grim`/`spectacle`；mss 10.2+ 可用 `backend="xshmgetimage"`

## 媒体播放

统一输出 `MediaInfo`。按平台拆实现。

### Windows：GSMTC

依赖：`winrt-Windows.Media.Control`（连带 `winrt-runtime`）。

```python
from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as SessionManager,
)

manager = await SessionManager.request_async()
session = manager.get_current_session()
props = await session.try_get_media_properties_async()
info = session.get_playback_info()
tl = session.get_timeline_properties()
```

| 字段 | 来源 |
|------|------|
| title / artist / album | `props.title` 等 |
| cover | `props.thumbnail`（IRandomAccessStreamReference） |
| state | `info.playback_status` |
| position_ms / duration_ms | `tl.position` / `tl.end_time` |
| app | `session.source_app_user_model_id` |

事件：`add_media_properties_changed`、`add_playback_info_changed`。订阅方负责 `remove_*` 退订。

注意：旧 `winsdk` / `winrt` 包已归档下架，不要用。**pycaw 是音量 API，拿不到歌名封面**，不能当 SMTC。

### macOS：AppleScript

主路径 `osascript`，分别驱动 Music.app 与 Spotify。

```applescript
tell application "Music"
  if player state is playing then
    set t to name of current track
    set a to artist of current track
    set al to album of current track
    set d to duration of current track
    set p to player position
  end if
end tell
```

- Music.app 的 `artwork` 是原始图数据，需落内存再编码；Spotify 给 `artwork url`
- 只能查指定 app，浏览器里播的拿不到
- 需要 Automation 权限（TCC），打包 .app 后首次运行会弹授权
- `osascript` 有 20–50ms 进程开销，适合 1–2s 轮询

MediaRemote 私有 API 在 macOS 15.4 起被 entitlement 掐死，普通进程不可用。若将来要覆盖任意播放器，可评估 `ungive/mediaremote-adapter` 并用 `test` 做降级探测，失败回落 AppleScript。

### Linux：MPRIS2

依赖：`jeepney`（同步、零依赖、MIT）。asyncio 路线可换 `dbus-next`。

- 总线名 `org.mpris.MediaPlayer2.*`，对象 `/org/mpris/MediaPlayer2`
- 接口 `org.mpris.MediaPlayer2.Player`
- Metadata 键：`xesam:title`、`xesam:artist`、`xesam:album`、`mpris:artUrl`、`mpris:length`（微秒）
- `PlaybackStatus`：`Playing` / `Paused` / `Stopped`
- `Position` 不触发 PropertiesChanged，进度需按 `Rate` 插值或轮询

注意：`mpris:artUrl` 可能是 `file://` 或 `https://`；多播放器在线时优先 `PlaybackStatus=Playing` 的那个；会话总线地址可能需从 `XDG_RUNTIME_DIR/bus` 推断。

## 进程列表

依赖：`psutil`。

```python
for proc in psutil.process_iter(["pid", "name", "exe", "cmdline"]):
    ...
```

### 白名单

- 配置为正则列表，`re.compile` 缓存
- 三路匹配 `name`、`basename(exe)`、`basename(cmdline[0])`，用 `fullmatch`
- 白名单匹配机器名，不匹配显示名
- 空名单等于不采集
- 同一 basename 去重聚合并带 `count`
- 默认排除 `* Helper`、`* Renderer`、`crashpad_handler` 等辅助进程

### 显示名（展示层做，采集层不做）

| 平台 | 做法 |
|------|------|
| Windows | 维护 exe 到显示名映射表，失败则显示 basename |
| macOS | 读 `*.app/Contents/MacOS/..` 外层 `Info.plist` 的 `CFBundleDisplayName` |
| Linux | 可查 `/usr/share/applications/*.desktop` 的 `Name=` |

异常吞 `NoSuchProcess`、`AccessDenied`；僵尸进程直接忽略。

## 系统负载

| 平台 | API |
|------|-----|
| 全平台 | `psutil.cpu_percent`、`psutil.virtual_memory` |
| Unix | `os.getloadavg()` |
| Windows | `load_avg` 传空数组 |

## 依赖

```text
mss>=10.2
Pillow>=12.3
psutil>=7.2
winrt-Windows.Media.Control   ; sys_platform == 'win32'
jeepney>=0.8                  ; sys_platform == 'linux'
```

macOS 媒体走标准库 `subprocess` + `osascript`，无三方依赖。

## 关键约束

1. 平台分支只允许出现在 `adapters/` 各平台实现文件里
2. 隐私短路在适配器入口，不是采集完再删字段
3. 截图必须本地模糊加 WebP，明文不出本机
4. 进程过滤在采集层完成，未通过的不进 payload
5. 所有输出可直接 `json.dumps`，封面给 bytes 或已换存 URL

## macOS 媒体补充

- 优先 `nowplaying-cli`（https://github.com/kirtan-shah/nowplaying-cli），可读系统 Now Playing（含 SPlayer 等）与封面 artworkData。
- 该工具非系统自带、仅 macOS，官方安装方式为 `brew install nowplaying-cli` 或源码 `make install`，GPL-3.0，**不要打进客户端包**。
- 客户端 setup 模块负责检测与引导安装；缺失时回落 AppleScript Music/Spotify。
- 依赖 MediaRemote 私有 API，系统升级可能失效。

## 进程可见应用

- `process_collect_all` 为真时按路径与排除表筛选用户可见应用（`/Applications`、`*.app/Contents/MacOS` 等）。
- 空白名单且 collect_all 为假时不采集（隐私默认拒绝）。
