# Protocol — JSON 传输规范

本文件定义客户端、服务端、前端之间的数据契约。改动本规范时必须同步更新三端代码。

## 通用约定

- 所有接口挂在 `/api/v1` 下。破坏性变更升版本号，不在 v1 内做不兼容修改。
- 请求与响应均为 `application/json; charset=utf-8`，截图二进制走独立接口或 base64 字段，默认 WebP。
- 时间戳一律为 UTC 毫秒整数（Unix epoch ms），字段名 `ts`。展示时区由前端处理。
- 客户端上报鉴权：请求头 `X-API-Key: <key>`。密钥在服务端配置与客户端本地配置中各存一份，不进 Git。
- 未知字段忽略，缺失可选字段按默认值处理。必填字段缺失返回 `400`。

## 错误响应

```json
{
  "ok": false,
  "error": {
    "code": "invalid_payload",
    "message": "field ts is required"
  }
}
```

| HTTP | code | 含义 |
|------|------|------|
| 400 | `invalid_payload` | 校验失败 |
| 401 | `unauthorized` | API Key 错误或缺失 |
| 403 | `forbidden` | 被拒绝（如 IP 已封禁） |
| 404 | `not_found` | 资源不存在 |
| 409 | `conflict` | 幂等冲突（可选） |
| 413 | `payload_too_large` | 体积超限 |
| 429 | `rate_limited` | 上报过于频繁 |

## 一、心跳上报

### `POST /api/v1/heartbeat`

客户端周期性上报一条完整快照。服务端以 `ts` 为准落库，不信任到达时间。

#### 请求体

```json
{
  "ts": 1761648000000,
  "client": {
    "id": "desktop-main",
    "platform": "macos",
    "version": "0.1.0"
  },
  "system": {
    "cpu_percent": 12.5,
    "memory_percent": 48.2,
    "load_avg": [2.1, 1.8, 1.6]
  },
  "media": {
    "state": "playing",
    "title": "Song Title",
    "artist": "Artist Name",
    "album": "Album Name",
    "app": "Music",
    "cover_url": "https://cdn.example.com/cover.webp",
    "position_ms": 42500,
    "duration_ms": 210000
  },
  "processes": [
    { "name": "Code", "count": 3 },
    { "name": "Safari", "count": 1 }
  ],
  "privacy": {
    "screenshot": true,
    "media": true,
    "processes": true,
    "system": true
  }
}
```

#### 字段说明

**`ts`** 心跳时间，必填，UTC 毫秒。

**`client`**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 客户端稳定标识，配置生成 |
| `platform` | string | 是 | `windows` / `macos` / `linux` |
| `version` | string | 否 | 客户端版本号 |

**`system`** 仅当 `privacy.system` 为 `true` 时必须完整；否则可省略或为 `null`。

| 字段 | 类型 | 说明 |
|------|------|------|
| `cpu_percent` | number | 0–100 |
| `memory_percent` | number | 0–100 |
| `load_avg` | number[3] | 1/5/15 分钟负载，Windows 下可为空数组 |

**`media`** 仅当 `privacy.media` 为 `true` 时上报；无播放时 `state` 为 `idle`，其余字段可空。

| 字段 | 类型 | 说明 |
|------|------|------|
| `state` | string | `playing` / `paused` / `idle` |
| `title` | string \| null | 歌名 |
| `artist` | string \| null | 歌手 |
| `album` | string \| null | 专辑 |
| `app` | string \| null | 播放器名 |
| `cover_url` | string \| null | 封面 URL，由服务端换存后的地址 |
| `position_ms` | int \| null | 播放进度 |
| `duration_ms` | int \| null | 总时长 |

**`processes`** 仅当 `privacy.processes` 为 `true` 时上报。已按客户端白名单过滤。

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 应用显示名 |
| `count` | int | 进程数，可选，默认 1 |

**`privacy`** 反馈客户端各开关实际状态，服务端据此决定接受哪些子块，并供前端显示采集范围。开关关闭的子块即使出现在请求里也应被服务端忽略。

#### 响应

```json
{
  "ok": true,
  "data": {
    "received_ts": 1761648000123,
    "screenshot_upload_url": "/api/v1/screenshot/desktop-main",
    "screenshot_expires_in": 60
  }
}
```

`screenshot_upload_url` 仅当 `privacy.screenshot` 为 `true` 时返回。客户端随后 `PUT` 截图。

### `PUT /api/v1/screenshot/{client_id}`

上传一张模糊后的桌面快照。

- `Content-Type: image/webp`
- 请求体为原始 WebP 字节
- 可选请求头 `X-Heartbeat-Ts` 对应心跳 `ts`
- 体积上限建议 512 KB，超限 `413`
- 响应：

```json
{
  "ok": true,
  "data": {
    "url": "/static/snapshots/desktop-main-latest.webp",
    "ts": 1761648000000
  }
}
```

服务端可只保留最新一张与按天的历史快照，过期由定时任务清理。

## 二、实时状态

### `GET /api/v1/status`

供 Web Dashboard 拉取。无需 API Key（只读公开状态），也可按部署环境关闭。

#### 查询参数

| 参数 | 默认 | 说明 |
|------|------|------|
| `client_id` | 配置的默认客户端 | 指定客户端 |

#### 响应

```json
{
  "ok": true,
  "data": {
    "online": true,
    "last_heartbeat_ts": 1761648000000,
    "client": {
      "id": "desktop-main",
      "platform": "macos",
      "version": "0.1.0"
    },
    "system": {
      "cpu_percent": 12.5,
      "memory_percent": 48.2,
      "load_avg": [2.1, 1.8, 1.6]
    },
    "media": {
      "state": "playing",
      "title": "Song Title",
      "artist": "Artist Name",
      "album": "Album Name",
      "app": "Music",
      "cover_url": "/static/covers/xxx.webp",
      "position_ms": 42500,
      "duration_ms": 210000
    },
    "processes": [
      { "name": "Code", "count": 3 }
    ],
    "screenshot": {
      "url": "/static/snapshots/desktop-main-latest.webp",
      "ts": 1761647990000,
      "width": 960,
      "height": 540
    },
    "privacy": {
      "screenshot": true,
      "media": true,
      "processes": true,
      "system": true
    }
  }
}
```

`online` 由服务端根据 `last_heartbeat_ts` 与阈值（建议 90 秒）计算，不落库。

### `GET /api/v1/stream`（可选）

SSE 实时推送。事件类型：

| event | data |
|-------|------|
| `status` | 与 `GET /api/v1/status` 的 `data` 相同 |
| `heartbeat` | 精简心跳（可不含截图） |
| `snapshot` | 截图更新通知 `{ "client_id", "ts", "url" }` |
| `message` | 新留言，见「四、留言」资源模型 |

单用户场景下前端优先短轮询 `GET /api/v1/status`（5–15 秒），SSE 作为增强。

## 三、日记

### 资源模型

```json
{
  "id": 1,
  "title": "标题",
  "content": "正文，纯文本或 Markdown",
  "mood": "calm",
  "tags": ["life"],
  "created_ts": 1761648000000,
  "updated_ts": 1761648000000
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | int | 响应 | 自增主键 |
| `title` | string | 是 | 最长 200 |
| `content` | string | 是 | 正文 |
| `mood` | string \| null | 否 | 情绪标签 |
| `tags` | string[] | 否 | 标签列表 |
| `created_ts` | int | 响应 | 创建时间 |
| `updated_ts` | int | 响应 | 更新时间 |

### 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/diaries` | 列表，支持 `?limit=&offset=&tag=` |
| GET | `/api/v1/diaries/{id}` | 详情 |
| POST | `/api/v1/diaries` | 新建，body 为上述模型去掉 `id`/时间戳 |
| PATCH | `/api/v1/diaries/{id}` | 局部更新 |
| DELETE | `/api/v1/diaries/{id}` | 删除 |

列表响应：

```json
{
  "ok": true,
  "data": {
    "items": [],
    "total": 0,
    "limit": 20,
    "offset": 0
  }
}
```

日记接口建议要求鉴权（写操作 `X-API-Key` 或前端登录），避免公开可写。

## 四、留言

### 资源模型

```json
{
  "id": 1,
  "author": "Sora",
  "content": "路过留个脚印",
  "created_ts": 1761648000000,
  "expose_ip": false,
  "location": null
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | int | 响应 | 自增主键 |
| `author` | string | 否 | 显示名，可空表示匿名，最长 50 |
| `content` | string | 是 | 正文，去空白后非空，最长 500 |
| `created_ts` | int | 响应 | 创建时间，UTC 毫秒 |
| `expose_ip` | bool | 否 | 是否允许公开 IP 属地，默认 `false` |
| `location` | string \| null | 响应 | IP 属地，仅 `expose_ip` 为 `true` 时返回 |

### 管理资源模型

管理端（`X-API-Key`）额外可见 `ip` 与始终返回的 `location`：

```json
{
  "id": 1,
  "author": "Sora",
  "content": "路过留个脚印",
  "created_ts": 1761648000000,
  "ip": "203.0.113.9",
  "location": "广东",
  "expose_ip": true
}
```

`location` 由服务端解析：国内精确到省，国外到国家，失败为 `未知`。

### 封禁资源模型

```json
{
  "id": 1,
  "ip": "203.0.113.9",
  "created_ts": 1761648000000
}
```

### 接口

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| GET | `/api/v1/messages` | 无 | 列表，倒序，`?limit=&offset=` |
| POST | `/api/v1/messages` | 无 | 发布留言，body 为 `{ "author"?, "content", "expose_ip"? }` |
| GET | `/api/v1/messages/admin` | `X-API-Key` | 管理列表，含 `ip` 与 `location` |
| DELETE | `/api/v1/messages/{id}` | `X-API-Key` | 删除单条留言 |
| GET | `/api/v1/messages/bans` | `X-API-Key` | 封禁列表 |
| POST | `/api/v1/messages/bans` | `X-API-Key` | 封禁 IP，body 为 `{ "ip" }` |
| DELETE | `/api/v1/messages/bans/{id}` | `X-API-Key` | 解封 |

列表响应：

```json
{
  "ok": true,
  "data": {
    "items": [],
    "total": 0,
    "limit": 20,
    "offset": 0
  }
}
```

`POST` 写入不需要 API Key，但要求客户端在线：最近心跳落在 online 窗口（建议 90 秒）内，否则返回 `409`（`conflict`，`Client offline`）。`content` 缺失或空白返回 `400`。同一来源写入过频返回 `429`（建议 60 秒 5 条）。被封 IP 写入返回 `403`（`forbidden`，`IP banned`）。

服务端在 `POST` 时记录客户端 IP（优先 `X-Forwarded-For` 第一段），并解析属地缓存到本地；属地查询只在服务端发起，失败时写 `未知`。

SSE `message` 事件在新留言落库后推送，data 为上述资源模型。前端发送表单在 `online` 为 `false` 时应禁用。

## 五、友情链接

### 资源模型

```json
{
  "id": 1,
  "name": "Name",
  "url": "https://example.com",
  "avatar_url": "https://example.com/avatar.png",
  "description": "一句话介绍",
  "sort": 10
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | int | 响应 | 自增主键 |
| `name` | string | 是 | 显示名 |
| `url` | string | 是 | 主页链接 |
| `avatar_url` | string \| null | 否 | 头像 |
| `description` | string \| null | 否 | 简介 |
| `sort` | int | 否 | 排序权重，越小越靠前 |

### 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/friends` | 列表，按 `sort` 升序 |
| POST | `/api/v1/friends` | 新建 |
| PATCH | `/api/v1/friends/{id}` | 更新 |
| DELETE | `/api/v1/friends/{id}` | 删除 |

前端只读列表可公开，写操作需 API Key。

## 六、GitHub 缓存

服务端定时抓取 GitHub 资料并缓存，前端不直连 GitHub。贡献热力图走 GitHub GraphQL `contributionsCollection`，需要个人访问令牌（PAT）。

### `GET /api/v1/github`

返回服务端定时抓取的 GitHub 资料，无需鉴权。

```json
{
  "ok": true,
  "data": {
    "login": "SoraSushi776",
    "name": "Sora",
    "bio": "…",
    "avatar_url": "…",
    "html_url": "https://github.com/SoraSushi776",
    "readme_html": "<article>…</article>",
    "contributions": {
      "total_last_year": 1234,
      "days": [
        { "date": "2025-01-01", "count": 3, "level": 1 }
      ]
    },
    "fetched_ts": 1761648000000
  }
}
```

`contributions.days` 为最近一年日粒度；`level` 为 0–4 热力等级。`fetched_ts` 为后台任务最近一次刷新时间。`readme_html` 已在服务端做有限标签清洗，前端仍可二次 sanitize。缓存为空时 `data` 为 `{}`。

### `POST /api/v1/github/token`

客户端推送 GitHub PAT，鉴权 `X-API-Key`。token 只进服务端本地 `secrets.json`，不进 Git，不出现在任何响应里。

#### 请求体

```json
{
  "token": "ghp_xxx",
  "login": "SoraSushi776"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `token` | string | 是 | GitHub PAT，最长 512 |
| `login` | string \| null | 否 | 热力图目标用户，缺省沿用服务端配置 |

#### 响应

```json
{
  "ok": true,
  "data": {
    "configured": true,
    "login": "SoraSushi776",
    "updated_ts": 1761648000000
  }
}
```

写入成功后服务端立即排队一次缓存刷新，之后仍由 APScheduler 周期刷新。

### 客户端字段

客户端本地配置与密钥对应关系：

| 位置 | 字段 | 说明 |
|------|------|------|
| `client.secrets.json` | `github_token` | GitHub PAT，0600 权限，与 `api_key` 同级 |
| 主配置（可选） | `github_login` | 目标 GitHub 用户，默认 `SoraSushi776` |

客户端保存设置后应调用 `POST /api/v1/github/token` 把 `github_token`（可带 `login`）推送到服务端，请求头带 `X-API-Key`。推送失败仅记日志，下次保存设置时重试。token 不写入心跳上报体。

## 七、站点设置

站点标题、描述与软件标签云区块标题，可在客户端设置页修改后推送到服务端。

### 资源模型

```json
{
  "title": "HeartBeat",
  "tagline": "个人主页与实时状态",
  "process_title": "TA的电脑上正在玩"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | 否 | 站点标题，最长 80，缺省 `HeartBeat` |
| `tagline` | string | 否 | 站点描述，最长 200，可为空 |
| `process_title` | string | 否 | 软件标签云区块标题，最长 80，缺省 `TA的电脑上正在玩` |

### 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/site` | 读取站点文案，无需鉴权 |
| PUT | `/api/v1/site` | 写入站点文案，body 为上述模型任意子集，鉴权 `X-API-Key` |

#### 响应

```json
{
  "ok": true,
  "data": {
    "title": "HeartBeat",
    "tagline": "个人主页与实时状态",
    "process_title": "TA的电脑上正在玩"
  }
}
```

设置存服务端 `data/secrets.json` 的 `site` 对象，不进 Git。`PUT` 为合并更新，仅提交需要修改的字段。`title` / `process_title` 提交空白值返回 `400`。前端 header 品牌与 ProcessCloud 标题读取该配置，未配置时回退默认值。

## 八、版本与兼容

- 客户端发送 `X-Client-Version` 可选头。
- 服务端对已废弃字段在响应中保留一个次版本周期。
- 新增字段不视为破坏性变更；删除或改义字段必须升 `/api/v2`。

## 九、体积与频率

| 项目 | 建议值 |
|------|--------|
| 心跳间隔 | 15–60 秒 |
| 心跳体（不含截图） | < 16 KB |
| 截图 | WebP，宽约 960–1280，模糊后 < 512 KB |
| 状态轮询 | 5–15 秒 |
| 状态响应 | < 32 KB |

客户端在隐私开关全关时仍可只发存活心跳（`client` + `ts`），用于在线指示。
