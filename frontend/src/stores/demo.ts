import type {
  Diary,
  FriendLink,
  GithubData,
  ProcessInfo,
  StatusData,
} from "../types/protocol"

function contributionDays(): { date: string; count: number; level: number }[] {
  const days: { date: string; count: number; level: number }[] = []
  const start = new Date()
  start.setUTCDate(start.getUTCDate() - 364)
  for (let i = 0; i < 365; i += 1) {
    const day = new Date(start)
    day.setUTCDate(start.getUTCDate() + i)
    const count = (i * 17 + 7) % 12
    days.push({
      date: day.toISOString().slice(0, 10),
      count,
      level: count < 2 ? 0 : count < 5 ? 1 : count < 8 ? 2 : count < 11 ? 3 : 4,
    })
  }
  return days
}

export function demoStatus(): StatusData {
  const now = Date.now()
  const processes: ProcessInfo[] = [
    { name: "Code", count: 3 },
    { name: "Safari", count: 1 },
    { name: "Music", count: 1 },
    { name: "WeChat", count: 2 },
    { name: "Terminal", count: 1 },
    { name: "Notes", count: 1 },
  ]
  return {
    online: true,
    last_heartbeat_ts: now - 8_000,
    client: { id: "desktop-main", platform: "macos", version: "0.1.0" },
    system: {
      cpu_percent: 23.4,
      memory_percent: 61.2,
      load_avg: [2.1, 1.8, 1.6],
    },
    media: {
      state: "playing",
      title: "Midnight City",
      artist: "M83",
      album: "Hurry Up, We're Dreaming",
      app: "Music",
      cover_url: "",
      position_ms: 82_000,
      duration_ms: 244_000,
    },
    processes,
    screenshot: null,
    privacy: {
      screenshot: true,
      media: true,
      processes: true,
      system: true,
    },
  }
}

export function demoDiaries(): Diary[] {
  const now = Date.now()
  return [
    {
      id: 3,
      title: "把 Dashboard 串起来了",
      content: "客户端采集、服务端入库、前端展示这条链终于跑通。截图本地模糊后再上传，隐私边界也守住了。",
      mood: "happy",
      tags: ["project", "heartbeat"],
      created_ts: now - 3600_000,
      updated_ts: now - 3600_000,
    },
    {
      id: 2,
      title: "夜里的城市",
      content: "窗外的灯一盏盏灭掉，屏幕上的热力图还亮着。今天也写了不少代码。",
      mood: "calm",
      tags: ["life"],
      created_ts: now - 86_400_000,
      updated_ts: now - 86_400_000,
    },
    {
      id: 1,
      title: "项目启动",
      content: "定下 PySide6 + FastAPI + Vue 的栈，先做心跳协议，再一层层搭采集与展示。",
      mood: "focus",
      tags: ["project"],
      created_ts: now - 3 * 86_400_000,
      updated_ts: now - 3 * 86_400_000,
    },
  ]
}

export function demoFriends(): FriendLink[] {
  return [
    {
      id: 1,
      name: "GitHub",
      url: "https://github.com",
      description: "代码与开源",
      sort: 1,
    },
    {
      id: 2,
      name: "Vue",
      url: "https://vuejs.org",
      description: "渐进式前端框架",
      sort: 2,
    },
    {
      id: 3,
      name: "FastAPI",
      url: "https://fastapi.tiangolo.com",
      description: "高性能 Python API",
      sort: 3,
    },
    {
      id: 4,
      name: "Qt for Python",
      url: "https://doc.qt.io/qtforpython-6/",
      description: "跨平台桌面界面",
      sort: 4,
    },
  ]
}

export function demoGithub(): GithubData {
  return {
    login: "SoraSushi776",
    name: "Sora",
    bio: "Building HeartBeat — a personal digital pulse dashboard.",
    avatar_url: "",
    html_url: "https://github.com/SoraSushi776",
    readme_html:
      "<p>跨平台个人状态 Dashboard：采集系统状态、正在播放与软件列表，在网页上实时展示。</p>",
    contributions: {
      total_last_year: 1284,
      days: contributionDays(),
    },
    fetched_ts: Date.now(),
  }
}
