import { computed, inject, onMounted, onUnmounted, ref, shallowRef, type InjectionKey } from "vue"
import {
  createMessage,
  fetchBackground,
  fetchDiaries,
  fetchFriends,
  fetchGithub,
  fetchMessages,
  fetchSite,
  fetchStatus,
} from "../api/http"
import { StatusStream, type StreamMode } from "../api/stream"
import {
  demoDiaries,
  demoFriends,
  demoGithub,
  demoMessages,
  demoStatus,
} from "./demo"
import type {
  Diary,
  FriendLink,
  GithubData,
  Message,
  SiteInfo,
  SnapshotEvent,
  StatusData,
} from "../types/protocol"

const ONLINE_WINDOW_MS = 90_000
const TICK_MS = 10_000

export class DashboardStore {
  readonly status = shallowRef<StatusData | null>(null)
  readonly diaries = ref<Diary[]>([])
  readonly friends = ref<FriendLink[]>([])
  readonly messages = ref<Message[]>([])
  readonly github = shallowRef<GithubData | null>(null)
  readonly nowMs = ref(Date.now())
  readonly streamMode = ref<StreamMode>("idle")
  readonly lightboxOpen = ref(false)
  readonly demoMode = ref(false)
  readonly backgroundUrl = ref("")
  readonly site = shallowRef<SiteInfo>({
    title: "HeartBeat",
    tagline: "个人主页与实时状态",
    process_title: "TA的电脑上正在玩",
  })

  private stream: StatusStream | null = null
  private clock: number | null = null

  readonly lastHeartbeatTs = computed(() => this.status.value?.last_heartbeat_ts ?? 0)

  readonly isOnline = computed(() => {
    const ts = this.lastHeartbeatTs.value
    return ts > 0 && this.nowMs.value - ts < ONLINE_WINDOW_MS
  })

  /** 首屏并行拉取状态、日记、友链、留言与 GitHub 资料 */
  async loadAll(): Promise<void> {
    await Promise.all([
      this.loadStatus(),
      this.loadDiaries(),
      this.loadFriends(),
      this.loadMessages(),
      this.loadGithub(),
      this.loadBackground(),
      this.loadSite(),
    ])
  }

  /** 拉取站点标题文案 */
  async loadSite(): Promise<void> {
    try {
      const data = await fetchSite()
      this.site.value = {
        title: data.title || "HeartBeat",
        tagline: data.tagline || "个人主页与实时状态",
        process_title: data.process_title || "TA的电脑上正在玩",
      }
    } catch {
      return
    }
  }

  /** 拉取站点背景图 */
  async loadBackground(): Promise<void> {
    try {
      const data = await fetchBackground()
      this.backgroundUrl.value = data.url ?? ""
    } catch {
      this.backgroundUrl.value = ""
    }
  }

  /** 拉取全量实时状态 */
  async loadStatus(): Promise<void> {
    try {
      this.status.value = await fetchStatus()
      this.demoMode.value = false
    } catch {
      this.status.value = demoStatus()
      this.demoMode.value = true
    }
  }

  /** 拉取日记列表 */
  async loadDiaries(): Promise<void> {
    try {
      const list = await fetchDiaries()
      this.diaries.value = list.items
    } catch {
      this.diaries.value = demoDiaries()
    }
  }

  /** 拉取友情链接 */
  async loadFriends(): Promise<void> {
    try {
      this.friends.value = await fetchFriends()
    } catch {
      this.friends.value = demoFriends()
    }
  }

  /** 拉取留言列表 */
  async loadMessages(): Promise<void> {
    try {
      const list = await fetchMessages()
      this.messages.value = list.items
    } catch {
      this.messages.value = demoMessages()
    }
  }

  /** 发布留言并在成功后刷新列表 */
  async sendMessage(author: string, content: string): Promise<void> {
    await createMessage({ author: author || undefined, content })
    await this.loadMessages()
  }

  /** 拉取 GitHub 缓存资料 */
  async loadGithub(): Promise<void> {
    try {
      const data = await fetchGithub()
      this.github.value = data && Object.keys(data).length > 0 ? data : demoGithub()
    } catch {
      this.github.value = demoGithub()
    }
  }

  /** 打开快照灯箱 */
  openLightbox(): void {
    this.lightboxOpen.value = true
  }

  /** 关闭快照灯箱 */
  closeLightbox(): void {
    this.lightboxOpen.value = false
  }

  /** 启动时钟与实时流，先全量后增量 */
  start(): void {
    this.stop()
    void this.loadAll()
    this.clock = window.setInterval(() => {
      this.nowMs.value = Date.now()
    }, TICK_MS)
    this.stream = new StatusStream({
      onStatus: (data) => this.applyStatus(data),
      onSnapshot: (data) => this.applySnapshot(data),
      onModeChange: (mode) => {
        this.streamMode.value = mode
      },
    })
    this.stream.start()
  }

  /** 停止时钟与实时流 */
  stop(): void {
    if (this.clock !== null) {
      window.clearInterval(this.clock)
      this.clock = null
    }
    this.stream?.stop()
    this.stream = null
  }

  private applyStatus(data: StatusData): void {
    this.status.value = data
    this.nowMs.value = Date.now()
  }

  private applySnapshot(event: SnapshotEvent): void {
    const current = this.status.value
    if (!current) {
      return
    }
    this.status.value = {
      ...current,
      screenshot: {
        url: event.url,
        ts: event.ts,
        width: current.screenshot?.width,
        height: current.screenshot?.height,
      },
    }
  }
}

export const DashboardKey: InjectionKey<DashboardStore> = Symbol("dashboard")

/** 注入 DashboardStore 单例 */
export function useDashboard(): DashboardStore {
  const store = inject(DashboardKey)
  if (!store) {
    throw new Error("DashboardStore not provided")
  }
  return store
}

/** 在挂载与卸载时启停 store */
export function useDashboardLifecycle(store: DashboardStore): void {
  onMounted(() => store.start())
  onUnmounted(() => store.stop())
}
