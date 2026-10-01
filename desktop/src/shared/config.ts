export type Language = 'zh-CN' | 'en-US'

export interface ServerConfig {
  base_url: string
  timeout_seconds: number
}

export interface PushConfig {
  enabled: boolean
  interval_seconds: number
  retry_backoff_seconds: number[]
  max_queue_size: number
}

export interface PrivacyConfig {
  collect_screenshot: boolean
  collect_media: boolean
  collect_system_load: boolean
}

export interface ScreenshotConfig {
  blur_radius: number
  scale: number
  quality: number
}

export interface AutostartConfig {
  enabled: boolean
}

export interface UiConfig {
  start_minimized: boolean
  language: Language
}

export interface SiteConfig {
  title: string
  tagline: string
  show_heatmap: boolean
  tags_title: string
  tags: string[]
  show_icp: boolean
  icp_text: string
  icp_keyword: string
  github_owner: string
  github_repo: string
}

export interface AppConfig {
  client_id: string
  setup_completed: boolean
  server: ServerConfig
  push: PushConfig
  privacy: PrivacyConfig
  screenshot: ScreenshotConfig
  autostart: AutostartConfig
  ui: UiConfig
  site: SiteConfig
}

export interface Secrets {
  api_key: string
  github_token: string
  github_login: string
}

export interface PushRecordView {
  ts: number
  ok: boolean
  detail: string
}
