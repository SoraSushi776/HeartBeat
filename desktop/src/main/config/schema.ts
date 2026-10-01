import { z } from 'zod'

export const HEARTBEAT_INTERVAL_RANGE = { min: 5, max: 3600 } as const
export const BLUR_RADIUS_RANGE = { min: 0, max: 100 } as const
export const SCALE_RANGE = { min: 0.05, max: 1 } as const
export const QUALITY_RANGE = { min: 1, max: 100 } as const

export const DEFAULT_BACKOFF_SECONDS: number[] = [0, 5, 15, 60, 300]

export const DEFAULT_SERVER = {
  base_url: 'http://127.0.0.1:8000',
  timeout_seconds: 10
}

export const DEFAULT_PUSH = {
  enabled: true,
  interval_seconds: 60,
  retry_backoff_seconds: DEFAULT_BACKOFF_SECONDS,
  max_queue_size: 100
}

export const DEFAULT_PRIVACY = {
  collect_screenshot: true,
  collect_media: true,
  collect_processes: true,
  collect_system_load: true
}

export const DEFAULT_SCREENSHOT = {
  blur_radius: 10,
  scale: 0.25,
  quality: 75
}

export const DEFAULT_AUTOSTART = { enabled: false }

export const LANGUAGES = ['zh-CN', 'en-US'] as const

export type Language = (typeof LANGUAGES)[number]

export const DEFAULT_UI: { start_minimized: boolean; language: Language } = {
  start_minimized: true,
  language: 'zh-CN'
}

export const DEFAULT_SITE = {
  title: 'HeartBeat',
  tagline: '个人主页与实时状态',
  process_title: 'TA的电脑上正在玩',
  show_heatmap: true,
  tags_title: '标签',
  tags: [] as string[],
  show_icp: false,
  icp_text: '萌ICP备20263011号',
  icp_keyword: '20263011',
  github_owner: 'SoraSushi776',
  github_repo: 'HeartBeat'
}

function text(fallback: string) {
  return z.string().catch(fallback)
}

function flag(fallback: boolean) {
  return z.boolean().catch(fallback)
}

function bounded(fallback: number, min: number, max: number) {
  return z
    .number()
    .catch(fallback)
    .transform((value) => Math.min(Math.max(value, min), max))
}

function boundedInt(fallback: number, min: number, max: number) {
  return z
    .number()
    .catch(fallback)
    .transform((value) => Math.min(Math.max(Math.round(value), min), max))
}

function stringList() {
  return z
    .array(z.unknown())
    .catch([])
    .transform((items) => items.filter((item): item is string => typeof item === 'string'))
}

function backoffTable() {
  return z
    .array(z.unknown())
    .catch(DEFAULT_BACKOFF_SECONDS)
    .transform((items) => {
      const numbers = items
        .filter((item): item is number => typeof item === 'number' && Number.isFinite(item))
        .map((item) => Math.max(Math.round(item), 0))
      return numbers.length > 0 ? numbers : [...DEFAULT_BACKOFF_SECONDS]
    })
}

export const serverSchema = z
  .object({
    base_url: text(DEFAULT_SERVER.base_url),
    timeout_seconds: bounded(DEFAULT_SERVER.timeout_seconds, 1, 120)
  })
  .catch(DEFAULT_SERVER)

export const pushSchema = z
  .object({
    enabled: flag(DEFAULT_PUSH.enabled),
    interval_seconds: boundedInt(
      DEFAULT_PUSH.interval_seconds,
      HEARTBEAT_INTERVAL_RANGE.min,
      HEARTBEAT_INTERVAL_RANGE.max
    ),
    retry_backoff_seconds: backoffTable(),
    max_queue_size: boundedInt(DEFAULT_PUSH.max_queue_size, 0, 100000)
  })
  .catch(DEFAULT_PUSH)

export const privacySchema = z
  .object({
    collect_screenshot: flag(DEFAULT_PRIVACY.collect_screenshot),
    collect_media: flag(DEFAULT_PRIVACY.collect_media),
    collect_processes: flag(DEFAULT_PRIVACY.collect_processes),
    collect_system_load: flag(DEFAULT_PRIVACY.collect_system_load)
  })
  .catch(DEFAULT_PRIVACY)

export const screenshotSchema = z
  .object({
    blur_radius: bounded(
      DEFAULT_SCREENSHOT.blur_radius,
      BLUR_RADIUS_RANGE.min,
      BLUR_RADIUS_RANGE.max
    ),
    scale: bounded(DEFAULT_SCREENSHOT.scale, SCALE_RANGE.min, SCALE_RANGE.max),
    quality: boundedInt(DEFAULT_SCREENSHOT.quality, QUALITY_RANGE.min, QUALITY_RANGE.max)
  })
  .catch(DEFAULT_SCREENSHOT)

export const autostartSchema = z.object({ enabled: flag(DEFAULT_AUTOSTART.enabled) }).catch(DEFAULT_AUTOSTART)

export const uiSchema = z
  .object({
    start_minimized: flag(DEFAULT_UI.start_minimized),
    language: z.enum(LANGUAGES).catch(DEFAULT_UI.language)
  })
  .catch(DEFAULT_UI)

export const siteSchema = z
  .object({
    title: text(DEFAULT_SITE.title),
    tagline: text(DEFAULT_SITE.tagline),
    process_title: text(DEFAULT_SITE.process_title),
    show_heatmap: flag(DEFAULT_SITE.show_heatmap),
    tags_title: text(DEFAULT_SITE.tags_title),
    tags: stringList(),
    show_icp: flag(DEFAULT_SITE.show_icp),
    icp_text: text(DEFAULT_SITE.icp_text),
    icp_keyword: text(DEFAULT_SITE.icp_keyword),
    github_owner: text(DEFAULT_SITE.github_owner),
    github_repo: text(DEFAULT_SITE.github_repo)
  })
  .catch(DEFAULT_SITE)

export const appConfigSchema = z.object({
  client_id: text(''),
  setup_completed: flag(false),
  server: serverSchema.default(DEFAULT_SERVER),
  push: pushSchema.default(DEFAULT_PUSH),
  privacy: privacySchema.default(DEFAULT_PRIVACY),
  screenshot: screenshotSchema.default(DEFAULT_SCREENSHOT),
  process_whitelist: stringList(),
  process_collect_all: flag(true),
  autostart: autostartSchema.default(DEFAULT_AUTOSTART),
  ui: uiSchema.default(DEFAULT_UI),
  site: siteSchema.default(DEFAULT_SITE)
})

export const secretsSchema = z.object({
  api_key: text(''),
  github_token: text(''),
  github_login: text('')
})

export type AppConfig = z.infer<typeof appConfigSchema>
export type Secrets = z.infer<typeof secretsSchema>
export type ServerConfig = z.infer<typeof serverSchema>
export type PushConfig = z.infer<typeof pushSchema>
export type PrivacyConfig = z.infer<typeof privacySchema>
export type ScreenshotConfig = z.infer<typeof screenshotSchema>
export type UiConfig = z.infer<typeof uiSchema>
export type SiteConfig = z.infer<typeof siteSchema>

export function defaultConfig(): AppConfig {
  return appConfigSchema.parse({})
}

export function defaultSecrets(): Secrets {
  return secretsSchema.parse({})
}
