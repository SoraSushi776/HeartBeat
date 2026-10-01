export type Platform = 'windows' | 'macos' | 'linux'
export type MediaState = 'playing' | 'paused' | 'idle'
export type Capability = 'screenshot' | 'media' | 'processes' | 'system'

export interface ClientInfo {
  id: string
  platform: Platform
  version: string
}

export interface SystemInfo {
  cpu_percent: number
  memory_percent: number
  load_avg: number[]
}

export interface MediaInfo {
  state: MediaState
  title: string | null
  artist: string | null
  album: string | null
  app: string | null
  cover_url: string | null
  cover_bytes: Buffer | null
  position_ms: number | null
  duration_ms: number | null
}

export interface ProcessInfo {
  name: string
  count: number
}

export interface PrivacyFlags {
  screenshot: boolean
  media: boolean
  processes: boolean
  system: boolean
}

export interface ScreenshotResult {
  webp: Buffer
  width: number
  height: number
}

export interface WireMedia {
  state: MediaState
  title: string | null
  artist: string | null
  album: string | null
  app: string | null
  cover_url: string | null
  position_ms: number | null
  duration_ms: number | null
}

export interface HeartbeatPayload {
  ts: number
  client: ClientInfo
  privacy: PrivacyFlags
  processes: ProcessInfo[]
  system: SystemInfo | null
  media: WireMedia | null
}

export const API_PREFIX = '/api/v1'
export const HEADER_API_KEY = 'X-API-Key'
export const HEADER_CLIENT_VERSION = 'X-Client-Version'
export const HEADER_HEARTBEAT_TS = 'X-Heartbeat-Ts'
export const ONLINE_TIMEOUT_MS = 90_000
export const DEFAULT_HEARTBEAT_INTERVAL_S = 60

export function emptyMedia(): MediaInfo {
  return {
    state: 'idle',
    title: null,
    artist: null,
    album: null,
    app: null,
    cover_url: null,
    cover_bytes: null,
    position_ms: null,
    duration_ms: null
  }
}

export function toWireMedia(media: MediaInfo | null): WireMedia | null {
  if (!media) {
    return null
  }
  return {
    state: media.state,
    title: media.title,
    artist: media.artist,
    album: media.album,
    app: media.app,
    cover_url: media.cover_url,
    position_ms: media.position_ms,
    duration_ms: media.duration_ms
  }
}

export function emptyFlags(): PrivacyFlags {
  return { screenshot: true, media: true, processes: true, system: true }
}

export const CAPABILITY_BY_FLAG: Record<Capability, keyof PrivacyFlags> = {
  screenshot: 'screenshot',
  media: 'media',
  processes: 'processes',
  system: 'system'
}
