import type { MediaInfo, Platform, ScreenshotResult, SystemInfo } from '../protocol'
import { currentPlatform } from './platform'
import type { PrivacyGate } from './privacy'
import { LinuxMediaAdapter } from './media/linux'
import { MacosMediaAdapter } from './media/macos'
import { WindowsMediaAdapter } from './media/windows'
import { ScreenshotAdapter, type ScreenshotEncodeOptions } from './screenshot/adapter'
import { SystemLoadAdapter } from './system/index'

export interface MediaAdapter {
  collect: (gate: PrivacyGate) => Promise<MediaInfo | null>
}

export interface CollectorConfig {
  screenshot: ScreenshotEncodeOptions
}

type MediaFactory = () => MediaAdapter

const MEDIA_FACTORIES: Record<Platform, MediaFactory> = {
  macos: () => new MacosMediaAdapter(),
  windows: () => new WindowsMediaAdapter(),
  linux: () => new LinuxMediaAdapter()
}

export function createMediaAdapter(platform: Platform = currentPlatform()): MediaAdapter {
  return MEDIA_FACTORIES[platform]()
}

export interface CollectorBundle {
  collectScreenshot: (gate: PrivacyGate) => Promise<ScreenshotResult | null>
  collectMedia: (gate: PrivacyGate) => Promise<MediaInfo | null>
  collectSystem: (gate: PrivacyGate) => Promise<SystemInfo | null>
  update: (config: CollectorConfig) => void
}

export class CollectorRegistry implements CollectorBundle {
  readonly screenshot: ScreenshotAdapter
  readonly media: MediaAdapter
  readonly system: SystemLoadAdapter

  constructor(config: CollectorConfig) {
    this.screenshot = new ScreenshotAdapter(config.screenshot)
    this.media = createMediaAdapter()
    this.system = new SystemLoadAdapter()
  }

  update(config: CollectorConfig): void {
    this.screenshot.updateOptions(config.screenshot)
  }

  async collectScreenshot(gate: PrivacyGate): Promise<ScreenshotResult | null> {
    return this.screenshot.collect(gate)
  }

  async collectMedia(gate: PrivacyGate): Promise<MediaInfo | null> {
    return this.media.collect(gate)
  }

  async collectSystem(gate: PrivacyGate): Promise<SystemInfo | null> {
    return this.system.collect(gate)
  }
}

export * from './privacy'
export * from './platform'
export * from './shell'
