# Frontend — Web Dashboard

个人主页与实时状态合并展示：动态心跳、音乐挂件、软件标签云、模糊快照、GitHub 简介与热力图、日记时间轴、友情链接。

## 选型

| 项 | 选择 | 说明 |
|----|------|------|
| 框架 | Vue 3 `<script setup>` | 组件化需求真实 |
| 构建 | Vite 5+ | 产出 `frontend/dist/` |
| UI 基座 | MDUI 2 | Material 3 Web Components |
| 自定义视觉 | 手写 CSS 变量 | Material You token |
| 实时 | SSE（EventSource） | 降级轮询 |
| 托管 | FastAPI `app.frontend()` | 单进程单端口 |
| 状态 | ref / computed | Pinia 可选 |

不引入：Material Web（官方维护模式）、wordcloud2/d3-cloud、Web Audio、重型 timeline 库。

## 目录

```text
frontend/
├── index.html
├── vite.config.ts
├── src/
│   ├── main.ts
│   ├── App.vue
│   ├── api/           fetch 与 EventSource 封装
│   ├── stores/        状态（可选 Pinia）
│   ├── styles/        Material You 变量与主题
│   └── components/
│       ├── LiveStatus.vue
│       ├── MediaCard.vue
│       ├── ProcessCloud.vue
│       ├── SnapshotLightbox.vue
│       ├── GithubPanel.vue
│       ├── Heatmap.vue
│       ├── DiaryTimeline.vue
│       └── FriendLinks.vue
└── dist/              构建产物，不进 Git
```

## 模块一：实时状态

| 组件 | 行为 |
|------|------|
| LiveStatus | 在线灯由 `now - last_heartbeat_ts` 判定，不另开状态字段 |
| MediaCard | 封面、歌名、歌手、进度、音波 |
| ProcessCloud | 软件标签云 |
| SnapshotLightbox | 点击查看模糊桌面快照 |

### 更新策略

| 数据 | 机制 | 频率 |
|------|------|------|
| 音乐 | SSE `music` 事件 | 曲目切换即推 |
| 播放进度 | 本地 rAF 插值 | 5–15s 校正 |
| 在线灯 | 前端定时算 | 10–30s |
| 系统负载 | SSE 或轮询 | 15–30s |
| 快照 | SSE `snapshot` | 变更时 |
| 日记友链 | REST | 打开面板时 |

首屏 `GET /api/v1/status` 拉全量，再用 SSE 增量。EventSource 不可用时降级 15s 轮询。

## 模块二：静态整合

| 组件 | 行为 |
|------|------|
| GithubPanel | README HTML、头像、简介，数据来自 `GET /api/v1/github` |
| Heatmap | 自绘 SVG/CSS Grid 53x7 |
| DiaryTimeline | 垂直时间轴 |
| FriendLinks | 卡片列表，按 sort |

热力图数据由服务端 APScheduler 缓存，token 不进浏览器。格子 10–12px，gap 3px，五档色阶，CSS 变量上色。

## 组件实现要点

### 音波

浏览器不播音频，**纯 CSS 条形动画**，不要 Web Audio。

```css
.bar {
  transform-origin: bottom;
  animation: wave 0.9s ease-in-out infinite alternate;
  animation-play-state: var(--play-state);
}
```

播放中 `running`，暂停 `paused` 或压低高度。`animation-delay` 错开相位。

### 标签云

Flex Chip，不是 Wordle 词云。

```css
.cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
```

字号按权重映射：`font-size: 12px + weight * k`。不要 wordcloud2.js、d3-cloud。

### 日记时间轴

左侧轴线用 `::before`，节点圆点加右侧卡片。移动端改卡片堆叠。按年月分组粘性标题。Vue 用 `TransitionGroup` 做进场。样式独立 CSS，不内联。

### 截图弹窗

**不再二次 blur**，采集层已固定模糊。

- 遮罩 `backdrop-filter: blur(12px)` 只糊弹窗背后的页面
- `role="dialog"` + Esc + 焦点陷阱
- `max-width: 90vw; max-height: 85vh; object-fit: contain`
- 动画只用 `opacity` 与 `scale`，不要对图片套 blur 动画

## 主题

Material You 变量：

```css
:root {
  --md-sys-color-primary: #6750a4;
  --md-sys-color-on-primary: #ffffff;
  --md-sys-color-surface: #fffbfe;
  --md-sys-color-on-surface: #1c1b1f;
  --md-sys-shape-corner-medium: 12px;
}
```

深浅色用 `prefers-color-scheme` 加 `data-theme="dark"` 手动切换。MDUI 提供基座组件，音波、热力图、时间轴、弹窗手写。

## 与服务端集成

开发：

```ts
// vite.config.ts
export default {
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
};
```

生产：

```python
app.frontend("/", directory="frontend/dist")
```

`app.frontend()` 处理 SPA 路由 fallback，API 路由优先。比裸 `StaticFiles` 更合适。

## 部署

单进程 FastAPI 托管 `dist/`，单用户装完即用。上公网时再拆 Nginx：

- 静态走 Nginx 缓存
- SSE 路径 `proxy_buffering off`，并加 `X-Accel-Buffering: no`
- `proxy_read_timeout` 调大或用心跳注释行保活

## 坑

1. SSE 经反代必须关缓冲，否则事件攒批
2. 在线状态不另开字段，前端算
3. 音波是装饰，不是频谱
4. 模糊只做一次，别在前端再 blur 快照本体
5. 避开 Material Web
6. 热力图数据在服务端，浏览器不持 token
7. 长 CSS 不进 HTML
8. `frontend/dist` 进 `.gitignore`
9. 前端只渲染服务端数据，不补采
10. 组件边界按挂件拆，不揉单文件

## 依赖

```text
vue@^3.5
vite@^5
mdui@^2
```

可选：`pinia`、`vue-router`（多面板时）。
