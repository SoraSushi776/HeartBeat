import type { AppConfig, PushRecordView, Secrets } from './config'

export type { PushRecordView } from './config'

export interface DiaryItem {
  id: number
  title: string
  content: string
  mood: string | null
  tags: string[]
  created_ts: number
  updated_ts: number
}

export interface DiaryList {
  items: DiaryItem[]
  total: number
  limit: number
  offset: number
}

export interface FriendItem {
  id: number
  name: string
  url: string
  avatar_url: string | null
  description: string | null
  sort: number
}

export interface ReplyItem {
  id: number
  message_id: number
  content: string
  created_ts: number
}

export interface MessageItem {
  id: number
  author: string
  content: string
  created_ts: number
  ip: string
  location: string
  expose_ip: boolean
  replies: ReplyItem[]
}

export interface MessageList {
  items: MessageItem[]
  total: number
  limit: number
  offset: number
}

export interface BanItem {
  id: number
  ip: string
  created_ts: number
}

export interface MediaView {
  state: 'playing' | 'paused' | 'idle'
  title: string | null
  artist: string | null
  album: string | null
  app: string | null
  cover_url: string | null
  position_ms: number | null
  duration_ms: number | null
}

export interface SystemView {
  cpu_percent: number
  memory_percent: number
  load_avg: number[]
}

export interface SnapshotView {
  media: MediaView | null
  coverDataUrl: string | null
  system: SystemView | null
  collectedAt: number
}

export interface SetupCheck {
  id: string
  labelKey: string
  ok: boolean
  detail: string
  actionId: string | null
}

export interface SetupReport {
  checks: SetupCheck[]
}

export interface ConfigBundle {
  config: AppConfig
  secrets: Secrets
  configPath: string
  secretsPath: string
  clientVersion: string
}

export interface SaveResult {
  bundle: ConfigBundle
  pushWarnings: string[]
}

export interface SnapshotEnvelope {
  snapshot: SnapshotView
}

export interface BackgroundUploadResult {
  cancelled: boolean
  bytes: number
  detail: string
}

export const IPC = {
  configLoad: 'config:load',
  configSave: 'config:save',
  appInfo: 'app:info',
  windowHide: 'window:hide',
  windowShow: 'window:show',
  diagnosticsSnapshot: 'diagnostics:snapshot',
  diagnosticsHistory: 'diagnostics:history',
  setupReport: 'setup:report',
  setupAction: 'setup:action',
  diaryList: 'diary:list',
  diaryCreate: 'diary:create',
  diaryUpdate: 'diary:update',
  diaryDelete: 'diary:delete',
  friendList: 'friend:list',
  friendCreate: 'friend:create',
  friendUpdate: 'friend:update',
  friendDelete: 'friend:delete',
  messageList: 'message:list',
  messageDelete: 'message:delete',
  messageReply: 'message:reply',
  banList: 'ban:list',
  banCreate: 'ban:create',
  banDelete: 'ban:delete',
  siteUploadBackground: 'site:background',
  eventPushResult: 'event:push-result'
} as const

export interface AppInfo {
  platform: string
  version: string
  electron: string
  chrome: string
  node: string
}

export type Unsubscribe = () => void

export interface HeartbeatBridge {
  app: {
    info: () => Promise<AppInfo>
    platform: string
    hide: () => Promise<void>
    show: () => Promise<void>
  }
  config: {
    load: () => Promise<ConfigBundle>
    save: (bundle: ConfigBundle) => Promise<SaveResult>
  }
  diagnostics: {
    snapshot: () => Promise<SnapshotView>
    history: () => Promise<PushRecordView[]>
    onPushResult: (listener: (record: PushRecordView) => void) => Unsubscribe
  }
  setup: {
    report: () => Promise<SetupReport>
    run: (actionId: string) => Promise<SetupReport>
  }
  diary: {
    list: () => Promise<DiaryList>
    create: (payload: Partial<DiaryItem>) => Promise<DiaryItem>
    update: (id: number, payload: Partial<DiaryItem>) => Promise<DiaryItem>
    remove: (id: number) => Promise<unknown>
  }
  friend: {
    list: () => Promise<FriendItem[]>
    create: (payload: Partial<FriendItem>) => Promise<FriendItem>
    update: (id: number, payload: Partial<FriendItem>) => Promise<FriendItem>
    remove: (id: number) => Promise<unknown>
  }
  message: {
    list: () => Promise<MessageList>
    remove: (id: number) => Promise<unknown>
    reply: (id: number, content: string) => Promise<unknown>
  }
  ban: {
    list: () => Promise<BanItem[]>
    create: (ip: string) => Promise<unknown>
    remove: (id: number) => Promise<unknown>
  }
  site: {
    uploadBackground: () => Promise<BackgroundUploadResult>
  }
}
