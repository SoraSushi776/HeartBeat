export interface ClientInfo {
  id: string
  platform: string
  version?: string | null
}

export interface SystemInfo {
  cpu_percent: number
  memory_percent: number
  load_avg: number[]
}

export type MediaState = "playing" | "paused" | "idle"

export interface MediaInfo {
  state: MediaState
  title?: string | null
  artist?: string | null
  album?: string | null
  app?: string | null
  cover_url?: string | null
  position_ms?: number | null
  duration_ms?: number | null
}

export interface ProcessInfo {
  name: string
  count?: number
}

export interface PrivacyFlags {
  screenshot: boolean
  media: boolean
  processes: boolean
  system: boolean
}

export interface ScreenshotInfo {
  url: string
  ts: number
  width?: number
  height?: number
}

export interface StatusData {
  online: boolean
  last_heartbeat_ts: number
  client: ClientInfo
  system?: SystemInfo | null
  media?: MediaInfo | null
  processes?: ProcessInfo[]
  screenshot?: ScreenshotInfo | null
  privacy?: PrivacyFlags
}

export interface Diary {
  id: number
  title: string
  content: string
  mood?: string | null
  tags?: string[]
  created_ts: number
  updated_ts: number
}

export interface FriendLink {
  id: number
  name: string
  url: string
  avatar_url?: string | null
  description?: string | null
  sort?: number
}

export interface Message {
  id: number
  author: string
  content: string
  created_ts: number
}

export interface MessageList {
  items: Message[]
  total: number
  limit: number
  offset: number
}

export interface ContributionDay {
  date: string
  count: number
  level: number
}

export interface GithubContributions {
  total_last_year: number
  days: ContributionDay[]
}

export interface GithubData {
  login: string
  name?: string | null
  bio?: string | null
  avatar_url?: string | null
  html_url?: string | null
  readme_html?: string | null
  contributions?: GithubContributions
  fetched_ts?: number
}

export interface SnapshotEvent {
  client_id: string
  ts: number
  url: string
}

export interface ApiError {
  code: string
  message: string
}

export interface ApiEnvelope<T> {
  ok: boolean
  data?: T
  error?: ApiError
}

export interface DiaryList {
  items: Diary[]
  total: number
  limit: number
  offset: number
}
