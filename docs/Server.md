# Server — FastAPI 服务端

接收客户端心跳，存 SQLite，向 Web Dashboard 提供状态与 CRUD，后台定时拉 GitHub 资料并清理过期数据。

## 选型

| 项 | 选择 | 说明 |
|----|------|------|
| 框架 | FastAPI 0.135+ | 原生 SSE，`app.frontend()` |
| 校验 | Pydantic v2 | 入参出参模型 |
| ORM | SQLModel | 一模型兼 ORM 与 API 模型 |
| 数据库 | SQLite | 单机单写者 |
| 定时 | APScheduler 3.11.x | 锁 `<4.0` |
| 实时 | SSE | 降级为轮询 |
| 鉴权 | `X-API-Key` | 写接口，读可公开 |
| 服务器 | Uvicorn | |

## 目录

```text
server/
├── main.py            应用装配与 lifespan
├── config.py          设置与密钥
├── dependencies.py    会话、鉴权依赖
├── middleware.py      请求守卫
├── models.py          SQLModel 表
├── schemas.py         Pydantic 出入参
├── routers/
│   ├── heartbeat.py
│   ├── status.py
│   ├── screenshot.py
│   ├── diaries.py
│   ├── friends.py
│   └── github.py
├── services/
│   ├── github_cache.py
│   ├── static_access.py
│   └── cleanup.py
└── db.py              引擎与建表
```

## 应用装配

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)

app = FastAPI(lifespan=lifespan)
app.include_router(heartbeat.router)
app.include_router(status.router)
```

注意：提供 `lifespan` 后 `@app.on_event` 不再触发，二者互斥。lifespan 只作用于主应用，挂载的 Sub App 不触发。

路由用 `APIRouter(prefix=..., dependencies=[Depends(require_api_key)])` 统一挂鉴权，不污染函数签名。`prefix` 不以 `/` 结尾。

## 数据模型

时间戳用 ISO8601 TEXT 或 Unix 毫秒整数，与 `docs/Protocol.md` 保持一致，本项目采用 UTC 毫秒整数 `ts`。

### heartbeat

| 列 | 类型 | 说明 |
|----|------|------|
| id | INTEGER PK | |
| ts | INTEGER | UTC 毫秒，建 `(ts DESC)` 索引 |
| client_id | TEXT | |
| payload_json | TEXT | 完整快照，含 system/media/processes/privacy |
| screenshot_path | TEXT \| NULL | |

高频写入（30s 一次）对 SQLite 无压力。截图文件不进库，只存路径。

### diary

| 列 | 类型 |
|----|------|
| id | INTEGER PK |
| title | TEXT NOT NULL |
| content | TEXT NOT NULL |
| mood | TEXT \| NULL |
| tags_json | TEXT |
| created_ts | INTEGER |
| updated_ts | INTEGER |

### friend

| 列 | 类型 |
|----|------|
| id | INTEGER PK |
| name | TEXT NOT NULL |
| url | TEXT NOT NULL |
| avatar_url | TEXT \| NULL |
| description | TEXT \| NULL |
| sort | INTEGER DEFAULT 0 |

### github_cache

单行或 JSON 文件缓存即可，字段见 `docs/Protocol.md` 第五节。

## 接口

对接 `docs/Protocol.md`。路由职责：

| 路由 | 职责 |
|------|------|
| `POST /api/v1/heartbeat` | 校验入库，按 privacy 子块决定接受范围，返回截图上传地址 |
| `PUT /api/v1/screenshot/{client_id}` | 存 WebP，限制体积，更新 latest |
| `GET /api/v1/status` | 由最近心跳组装实时状态，`online` 现算不落库 |
| `GET /api/v1/stream` | SSE 推送 status / heartbeat / snapshot |
| `CRUD /api/v1/diaries` | 日记 |
| `CRUD /api/v1/friends` | 友链 |
| `GET /api/v1/github` | 读 GitHub 缓存 |
| `POST /api/v1/github/token` | 存客户端推送的 PAT，排队刷新缓存 |

### 状态组装

```text
online = (now - last_heartbeat_ts) < 90_000
```

不设独立 online 字段，避免双写不一致。music / processes / screenshot 读最近一条心跳；GitHub 读缓存表。

### SSE

```python
from fastapi.sse import EventSourceResponse, ServerSentEvent

@router.get("/stream", response_class=EventSourceResponse)
async def stream() -> AsyncIterable[ServerSentEvent]:
    ...
```

FastAPI 0.135+ 内置 SSE，不需要 `sse-starlette`。事件类型 `status`、`heartbeat`、`snapshot`。前端降级为 5–15 秒轮询 `GET /status` 也可接受。

## 持久层

SQLModel：

```python
class Heartbeat(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ts: int = Field(index=True)
    ...
```

- 一套模型走 CRUD 与 API 序列化
- 复杂查询可混用 `sqlalchemy.select()` / `text()`
- 禁止在路由里写裸 SQL
- `session.exec()` 与 `session.execute()` 返回类型不同，混用时留意

## 定时任务

`BackgroundScheduler(timezone="UTC")` 挂 lifespan。时区统一 UTC，避开 DST。

| 任务 | 触发 | 动作 |
|------|------|------|
| `github_cache` | 每 30 分钟 Interval | 用 PAT 走 GraphQL 拉热力图，拉 README 并做有限标签清洗，写缓存 |
| `cleanup` | 每日 04:00 Cron | 删超期心跳与对应截图文件 |

```python
scheduler.add_job(fetch_github_cache, IntervalTrigger(minutes=30), id="github_cache", replace_existing=True)
```

`replace_existing=True` 防热重载重复注册。GitHub 拉取用 `httpx`，失败记日志不抛垮调度器。

## 鉴权

```python
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def require_api_key(key: str = Depends(api_key_header)) -> str:
    if not secrets.compare_digest(key, settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return key
```

| 接口 | 鉴权 |
|------|------|
| POST /heartbeat、PUT /screenshot | 要 |
| POST /github/token | 要 |
| GET /status、/github、/diaries、/friends | 公开（内网单机） |
| POST/PATCH/DELETE /diaries、/friends | 要 |

密钥从环境变量或本地配置读，不进 Git。比较用 `secrets.compare_digest`。GitHub PAT 由客户端推到 `POST /github/token`，落 `data/secrets.json`，响应与日志均不得回显。

## 静态资源与暴露面

`data_dir` 不再整体挂载到 `/static`，只逐个挂载公开图片目录。`heartbeat.db`（含留言 IP 与归属地）和 `secrets.json`（`api_key`、`github_token`）拿不到。

| 路径 | 来源 | 说明 |
|------|------|------|
| `/` | `frontend/dist` | `app.frontend()` 挂载的 SPA |
| `/static/snapshots` | `data/snapshots` | 模糊后的截图 |
| `/static/backgrounds` | `data/backgrounds` | 站点背景 |
| `/static/covers` | `data/covers` | 专辑封面 |
| 其它 `/static/**` | 无 | 一律 404 |

`StaticAccessPolicy` 决定哪些路径可公开：首段必须在 `PUBLIC_DIR_NAMES` 内，文件名不得是 `BLOCKED_NAMES`，后缀必须在 `PUBLIC_SUFFIXES`（图片）内，含 `..` 或点开头一律拒绝。`StaticGuardMiddleware` 在路由前拦截，命中写 warning 日志。新增公开目录要同时改这两个集合。

`/docs`、`/redoc`、`/openapi.json` 默认不注册（FastAPI 的 `docs_url` 等传 `None`），`HEARTBEAT_DOCS_ENABLED=true` 才打开。

## 数据保留

- 心跳默认保留 90 天，可配
- 截图默认保留最新一张加按天一张，清理任务同步删文件
- 日记、友链不自动过期

## 配置

| 项 | 来源 |
|----|------|
| `api_key` | 环境变量或 `secrets.json` |
| `github_token` | 环境变量或 `secrets.json`，由 `POST /github/token` 写入 |
| `database_url` | 默认 `sqlite:///./data.db` |
| `heartbeat_retention_days` | 默认 90 |
| `online_timeout_ms` | 默认 90000 |
| `github_login` | 热力图目标用户，`secrets.json` 或环境变量 |
| `cors_origains` | 开发期 Vite 源 |
| `docs_enabled` | 默认 false，为 true 才注册 `/docs`、`/redoc`、`/openapi.json` |

## 依赖

```text
fastapi>=0.135.0
uvicorn[standard]>=0.30.0
sqlmodel>=0.0.22
pydantic>=2.7.0
pydantic-settings>=2.3.0
apscheduler>=3.11.0,<4.0
httpx>=0.27.0
```

## 坑

1. `lifespan` 与 `on_event` 互斥，只用前者
2. APScheduler 4.x 仍是 alpha，锁 `<4.0`
3. 调度器时区固定 UTC
4. SSE 经 Nginx 必须 `proxy_buffering off`
5. 单 worker 足够；多 worker 时 SSE 需粘性或广播
6. 入参校验在 Pydantic 层做完，坏数据 400 拒绝
