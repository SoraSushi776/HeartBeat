import { logger } from './logger'
import { CollectorRegistry, type CollectorBundle, type CollectorConfig } from './adapters/index'
import { PrivacyGate } from './adapters/privacy'
import { currentPlatform } from './adapters/platform'
import { ApiError, HeartbeatApi } from './api'
import { toCoverJpeg } from './imaging'
import {
  toWireMedia,
  type HeartbeatPayload,
  type MediaInfo,
  type Platform,
  type PrivacyFlags,
  type ProcessInfo,
  type ScreenshotResult,
  type SystemInfo
} from './protocol'

export interface PushRecord {
  ts: number
  ok: boolean
  detail: string
}

export interface DiagnosticsSnapshot {
  media: MediaInfo | null
  processes: ProcessInfo[]
  system: SystemInfo | null
  coverBytes: Buffer | null
  collectedAt: number
}

export interface CollectorRuntimeConfig {
  clientId: string
  clientVersion: string
  pushEnabled: boolean
  intervalSeconds: number
  backoffSeconds: number[]
  privacy: PrivacyFlags
  collectors: CollectorConfig
}

export interface CollectorHandlers {
  onSnapshot?: (payload: HeartbeatPayload) => void
  onPushResult?: (record: PushRecord) => void
}

const HISTORY_LIMIT = 20

export function backoffDelaySeconds(table: number[], attempt: number): number {
  if (table.length === 0) {
    return 0
  }
  const index = Math.min(Math.max(attempt, 0), table.length - 1)
  return table[index]
}

export class HeartbeatCollector {
  private timer: NodeJS.Timeout | null = null
  private attempt = 0
  private running = false
  private gate: PrivacyGate
  private registry: CollectorBundle
  private history: PushRecord[] = []

  constructor(
    private api: HeartbeatApi,
    private config: CollectorRuntimeConfig,
    private handlers: CollectorHandlers = {},
    registry?: CollectorBundle
  ) {
    this.gate = new PrivacyGate(config.privacy)
    this.registry = registry ?? new CollectorRegistry(config.collectors)
  }

  get pushHistory(): PushRecord[] {
    return [...this.history]
  }

  get privacyFlags(): PrivacyFlags {
    return this.gate.flags
  }

  start(): void {
    if (!this.config.pushEnabled) {
      logger.info('Push disabled, collector idle')
      return
    }
    this.schedule(0)
    logger.info(`Collector started, interval=${this.config.intervalSeconds}s`)
  }

  stop(): void {
    if (this.timer) {
      clearTimeout(this.timer)
      this.timer = null
    }
    logger.info('Collector stopped')
  }

  applyConfig(config: CollectorRuntimeConfig): void {
    this.config = config
    this.gate.update(config.privacy)
    this.registry.update(config.collectors)
    if (this.timer) {
      clearTimeout(this.timer)
      this.timer = null
    }
    if (config.pushEnabled) {
      this.attempt = 0
      this.schedule(0)
    }
  }

  async collectDiagnostics(): Promise<DiagnosticsSnapshot> {
    const media = await this.registry.collectMedia(this.gate)
    const coverBytes = media?.cover_bytes ?? null
    return {
      media,
      processes: await this.registry.collectProcesses(this.gate),
      system: await this.registry.collectSystem(this.gate),
      coverBytes,
      collectedAt: Date.now()
    }
  }

  async tick(): Promise<PushRecord> {
    const screenshot = await this.registry.collectScreenshot(this.gate)
    const media = await this.registry.collectMedia(this.gate)
    const coverJpeg = await toCoverJpeg(media?.cover_bytes ?? null)
    const payload = await this.buildPayload(media, coverJpeg)
    this.handlers.onSnapshot?.(payload)

    let record: PushRecord
    try {
      const response = await this.api.heartbeat(payload)
      this.attempt = 0
      record = { ts: payload.ts, ok: true, detail: 'heartbeat ok' }
      const uploadUrl = response.screenshot_upload_url
      if (uploadUrl && screenshot) {
        await this.uploadScreenshot(uploadUrl, payload.ts, screenshot)
      }
    } catch (error) {
      this.attempt += 1
      const message = error instanceof ApiError ? error.message : String(error)
      record = { ts: payload.ts, ok: false, detail: message }
      logger.warn(`Heartbeat failed, attempt=${this.attempt}: ${message}`)
    }
    this.record(record)
    this.schedule(this.nextDelaySeconds(record.ok))
    return record
  }

  private nextDelaySeconds(ok: boolean): number {
    if (ok) {
      return this.config.intervalSeconds
    }
    return Math.max(backoffDelaySeconds(this.config.backoffSeconds, this.attempt), 1)
  }

  private schedule(delaySeconds: number): void {
    if (!this.config.pushEnabled) {
      return
    }
    const delayMs = Math.max(delaySeconds, 0) * 1000
    this.timer = setTimeout(() => {
      void this.runTick()
    }, delayMs)
  }

  private async runTick(): Promise<void> {
    if (this.running) {
      return
    }
    this.running = true
    try {
      await this.tick()
    } catch (error) {
      logger.error(`Collector tick crashed: ${String(error)}`)
    } finally {
      this.running = false
    }
  }

  private async buildPayload(
    media: MediaInfo | null,
    coverJpeg: Buffer | null
  ): Promise<HeartbeatPayload> {
    let mediaForWire: MediaInfo | null = media ? { ...media, cover_url: null } : null
    if (coverJpeg) {
      try {
        const coverUrl = await this.api.putCover(coverJpeg)
        if (coverUrl && mediaForWire) {
          mediaForWire = { ...mediaForWire, cover_url: coverUrl }
        }
      } catch (error) {
        logger.warn(`Cover upload failed: ${String(error)}`)
      }
    }
    return {
      ts: Date.now(),
      client: {
        id: this.config.clientId,
        platform: currentPlatform() as Platform,
        version: this.config.clientVersion
      },
      privacy: this.gate.flags,
      processes: await this.registry.collectProcesses(this.gate),
      system: await this.registry.collectSystem(this.gate),
      media: toWireMedia(mediaForWire)
    }
  }

  private async uploadScreenshot(
    uploadUrl: string,
    ts: number,
    screenshot: ScreenshotResult
  ): Promise<void> {
    try {
      await this.api.putScreenshot(uploadUrl, screenshot.webp, ts)
    } catch (error) {
      this.record({ ts, ok: false, detail: `screenshot: ${String(error)}` })
      logger.warn(`Screenshot upload failed: ${String(error)}`)
    }
  }

  private record(record: PushRecord): void {
    this.history = [record, ...this.history].slice(0, HISTORY_LIMIT)
    this.handlers.onPushResult?.(record)
  }
}
