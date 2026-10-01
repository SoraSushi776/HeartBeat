# HeartBeat

跨平台个人状态 Dashboard（数字心跳）。桌面客户端采集系统负载、正在播放的音乐、运行中的软件与模糊后的桌面快照，定时上报服务端；Web 端把实时状态与个人主页（GitHub 简介与热力图、日记时间轴、友情链接）合并展示。

## 功能

- **实时状态**：在线 / 离线指示（依据最近一次心跳时间判定）、音乐播放挂件、软件标签云、模糊快照弹窗
- **个人主页**：GitHub 简介与贡献热力图、日记时间轴、友情链接卡片
- **客户端**：Electron + React 桌面端，Material You 界面 + 系统托盘，全局推送开关、开机自启、细粒度隐私开关、软件白名单、截图模糊与缩放可配
- **采集适配**：Windows / macOS / Linux 统一抽象，截图本地高斯模糊并压成 WebP 后再离开本机
- **服务端**：FastAPI + SQLite + APScheduler，心跳上报、状态查询、日记与友情链接 CRUD，定时缓存 GitHub 资料并清理过期快照

## 架构

```text
[ Electron + React 客户端 ]
  ├── 跨平台采集适配器（截图 / 媒体 / 进程 / 系统负载）
  ├── 隐私开关与配置界面
  └── 异步推送 ──► [ FastAPI 服务端 ] ──► [ SQLite ]
                          │
                          └── 托管 [ Vue Web Dashboard ]
```

模块说明见 `docs/`：`Client.md`、`Adapters.md`、`Server.md`、`Frontend.md`、`Protocol.md`、`Packaging.md`。协议细节见 `docs/Protocol.md`，整体设计见 `OUTLINE.md`。

## 环境要求

- Python 3.10+
- Node.js 18+ 与 npm（构建前端时需要）
- 桌面客户端需要 Node.js 22+ 与 npm

## 安装

```bash
git clone <repo-url> HeartBeat
cd HeartBeat

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

平台专属媒体采集依赖已按系统标记写入 `requirements.txt`：Windows 自动装 `winrt-Windows.Media.Control`，Linux 自动装 `jeepney`。macOS 走系统脚本采集，无额外包。

也可按 `pyproject.toml` 的 extras 安装：

```bash
pip install -e ".[windows]"        # 或 .[linux]
pip install -e ".[dev]"
```

## 配置

服务端配置经环境变量与 `data/secrets.json` 读取，环境变量优先：

| 变量 | 说明 | 默认 |
|------|------|------|
| `HEARTBEAT_API_KEY` | 写接口鉴权密钥 | 未设置时自动生成并写入 `data/secrets.json` |
| `HEARTBEAT_DATA_DIR` | 数据目录（数据库、快照、密钥） | `data` |
| `HEARTBEAT_HOST` | 监听地址 | `127.0.0.1` |
| `HEARTBEAT_PORT` | 监听端口 | `8000` |
| `HEARTBEAT_GITHUB_TOKEN` | 拉取 GitHub README / 热力图的 PAT | 可选 |
| `HEARTBEAT_GITHUB_LOGIN` | 展示的 GitHub 用户名 | 可选 |
| `HEARTBEAT_CORS_ORIGINS` | 额外允许的跨域来源 | 空 |

`data/secrets.json` 不进 Git，可存 `api_key`、`github_token`、`github_login` 与站点文案（`site`）。

桌面端配置与 API 密钥保存在本地配置文件（macOS 为 `~/Library/Application Support/HeartBeat/`），在界面里设置服务端 URL、API Key、隐私开关、软件过滤白名单与截图参数。

## 部署

### 1. 构建前端

```bash
bash scripts/build_frontend.sh
```

等价于进入 `frontend/` 执行 `npm install` 与 `npm run build`，产物在 `frontend/dist/`。服务端启动时会自动托管该目录。

### 2. 启动服务端

```bash
bash scripts/run_server.sh
# 或
python -m heartbeat.server.main
# 或安装后的入口
heartbeat-server
```

默认监听 `http://127.0.0.1:8000`。开放到公网时设置 `HEARTBEAT_HOST=0.0.0.0`，并用反向代理终结 TLS、限制写接口访问。

主要接口：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/heartbeat` | 客户端心跳上报（需 `X-API-Key`） |
| GET | `/api/v1/status` | 实时状态 |
| GET | `/api/v1/stream` | 实时状态 SSE 流 |
| PUT | `/api/v1/screenshot/{client_id}` | 上传模糊截图 |
| CRUD | `/api/v1/diaries` | 日记 |
| CRUD | `/api/v1/friends` | 友情链接 |
| GET/PUT | `/api/v1/site` | 站点文案 |
| GET | `/api/v1/github` | GitHub 简介与热力图缓存 |
| CRUD | `/api/v1/messages` | 留言板 |
| GET/PUT | `/api/v1/background` | 站点背景图 |

读接口可公开访问，写接口需请求头 `X-API-Key`。完整列表见 `http://127.0.0.1:8000/docs`。

### 3. 启动客户端

先在图形界面里填好服务端 URL 与 API Key，再常驻托盘运行：

```bash
cd desktop
npm install
npm run dev
```

支持最小化到系统托盘、开机自启。各隐私开关关闭的能力不会被采集，也不会进入上报数据。

### 4. 测试与检查

```bash
pytest
ruff check .
```

## 打包客户端

桌面端由 electron-vite 构建，产物在 `desktop/out/`：

```bash
cd desktop
npm run build          # 类型检查 + 打包三端产物
```

构建产物与安装器配置不进 Git。

## 项目结构

```text
desktop/        Electron + React 桌面客户端
heartbeat/
├── adapters/   跨平台采集适配器（截图、媒体、进程、系统负载）
├── server/     FastAPI 服务端与 SQLite 存储
└── protocol/   上报与传输协议模型
frontend/       Vue Web Dashboard
docs/           模块与系统说明文档
scripts/        打包与构建脚本
tests/          测试
```

## License

见 [LICENSE](LICENSE)。
