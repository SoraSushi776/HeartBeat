# 项目设计方案与实施大纲

本项目旨在构建一个跨平台的个人状态 Dashboard（数字心跳/ Digital Pulse），通过客户端收集系统状态、多媒体播放信息及运行应用，并在前端网页实时动态展示。

## **一、 系统架构设计**

```text
[ 跨平台图形客户端 (PySide6 / PyQt6) ]
  ├── 跨平台采集适配器 (Windows / macOS / Linux)
  ├── 本地功能开关与配置界面
  └── 异步推送层 (WebSocket / HTTPS POST) -> [ 服务端 API (FastAPI) ]
                                                        │
                                                   [ SQLite 数据库 ]
                                                        │
                                              [ 前端 Web Dashboard ]
```

## **二、 客户端架构与技术细节 (Client)**

客户端采用 **PySide6 (Qt for Python)** 搭建 GUI，结合异步多线程机制（如 QThread 或 asyncio 集成）实现界面与采集解耦。

### **1\. GUI 界面设计 (Qt/PySide6)**

> * **主控开关**：全局推送使能、开机自启等。  
> * **细粒度隐私开关**：  
  * 允许/禁止 获取屏幕截图及高斯模糊  
  * 允许/禁止 获取正在播放的音乐  
  * 允许/禁止 获取运行中的软件列表  
  * 允许/禁止 获取系统负载与存活状态  
> * **配置面板**：服务端 URL、 API 密钥、软件过滤白名单配置、截图模糊半径与缩放比例调整。  
> * **系统托盘集成**：支持最小化到系统托盘（System Tray），静默后台运行。

### **2\. 跨平台采集适配层 (Cross-platform Adapters)**

针对不同操作系统的底层差异，建立统一抽象接口层：

#### **A. 屏幕截图与高斯模糊 (Cross-Platform)**

> * 使用 **Pillow (PIL)** 的 ImageGrab 扩展，或 **mss** 库（跨平台高性能截图）。  
> * 本地完成高斯模糊与 WebP 压缩，保护隐私并降低网络开销：

```python
import io
from PIL import ImageFilter, ImageGrab


def get_blurred_screenshot(radius=25, scale=0.5) -> bytes:
    # 跨平台截屏
    screenshot = ImageGrab.grab()
    new_size = (int(screenshot.width * scale), int(screenshot.height * scale))
    screenshot = screenshot.resize(new_size)

    # 本地模糊
    blurred = screenshot.filter(ImageFilter.GaussianBlur(radius))

    buffer = io.BytesIO()
    blurred.save(buffer, format="WEBP", quality=75)
    return buffer.getvalue()
```

#### **B. 正在播放的音乐提取 (Media Control)**

> * **Windows**: 使用 winsdk 或 pycaw 调用原生 **SMTC (System Media Transport Controls)** 接口。  
> * **macOS**: 通过 pyobjc 或 AppleScript（osascript）读取 Apple Music / Spotify 等播放器 API。  
> * **Linux**: 使用 dbus-python 或 jeepney 监听 **MPRIS2 D-Bus** 接口（符合 Linux 桌面媒体标准）。

#### **C. 进程列表过滤 (Process Monitor)**

> * 使用 **psutil.process\_iter()** 提取应用名称。  
> * 结合正则白名单过滤机制，只上报用户允许透出的知名软件。

### **3\. 打包与分发 (Packaging)**

> * 使用 **PyInstaller** 或 **Nuitka** 打包为单文件/安装包：  
  * **Windows**: 打包为 .exe，内置可配置的自启注册表项。  
  * **macOS**: 打包为 .app 应用程序。  
  * **Linux**: 打包为 .AppImage 或二进制执行文件。

## **三、 服务端与前端设计 (Server & Frontend)**

### **1\. 后端服务 (FastAPI \+ SQLite)**

* **API 接口**：  
  * POST /api/v1/heartbeat：接收客户端上报的数据。  
  * GET /api/v1/status：供前端获取实时状态。  
  * CRUD /api/v1/diaries：日记增删改查。  
  * CRUD /api/v1/friends：友情链接管理。  

* **后台异步任务 (APScheduler)**：  
  * 每半小时定时更新并缓存 GitHub README (Bio) 及 Contribution Graph (热力图)。  
  * 定期清理数据库中的历史过期快照与老旧数据。

### **2\. 前端展示 (Dashboard Window)**

* **模块一：实时状态（动态心跳）**  
  * 在线/离线指示灯（依据最近一次心跳时间自动判定）。  
  * 音乐播放器小挂件（带封面、歌名、歌手与跳动音波图）。  
  * 运行软件列表标签云。  
  * 点击弹窗查看高斯模糊后的桌面快照。  
* **模块二：静态整合（个人主页）**  
  * GitHub 个人介绍与热力图。  
  * 日记时间轴。  
  * 友情链接卡片。

## **四、 开发路线图**

1. **Phase 1**：搭建 FastAPI 后端与 SQLite ORM 结构，定义 JSON 传输规范。  
2. **Phase 2**：编写跨平台系统信息采集模块（系统负载、媒体状态、进程过滤、模糊截图）。  
3. **Phase 3**：使用 PySide6 开发图形客户端，引入配置项持久化（QSettings/JSON）与各功能逻辑开关。  
4. **Phase 4**：完成前端界面绘制（合并 Github 个人主页与动态心跳板块）。  
5. **Phase 5**：多平台构建测试（Windows / macOS / Linux）与 PyInstaller 编译打包。

