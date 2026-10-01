import type { MediaInfo, Platform, ProcessInfo, ScreenshotResult, SystemInfo } from '../protocol'
import { currentPlatform } from './platform'
import type { PrivacyGate } from './privacy'
import { LinuxMediaAdapter } from './media/linux'
import { MacosMediaAdapter } from './media/macos'
import { WindowsMediaAdapter } from './media/windows'
import { ProcessFilter } from './processes/filter'
import { SystemInformationProcessAdapter } from './processes/index'
import { ScreenshotAdapter, type ScreenshotEncodeOptions } from './screenshot/adapter'
import { SystemLoadAdapter } from './system/index'

export interface MediaAdapter {
  collect: (gate: PrivacyGate) => Promise<MediaInfo | null>
}

export interface CollectorConfig {
  processWhitelist: string[]
  processCollectAll: boolean
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

export class CollectorRegistry {
  readonly screenshot: ScreenshotAdapter
  readonly media: MediaAdapter
  readonly processes: SystemInformationProcessAdapter
  readonly system: SystemLoadAdapter

  constructor(config: CollectorConfig) {
    this.screenshot = new ScreenshotAdapter(config.screenshot)
    this.media = createMediaAdapter()
    this.processes = new SystemInformationProcessAdapter(buildFilter(config))
    this.system = new SystemLoadAdapter()
  }

  update(config: CollectorConfig): void {
    this.screenshot.updateOptions(config.screenshot)
    this.processes.updateFilter(buildFilter(config))
  }

  async collectScreenshot(gate: PrivacyGate): Promise<ScreenshotResult | null> {
    return this.screenshot.collect(gate)
  }

  async collectMedia(gate: PrivacyGate): Promise<MediaInfo | null> {
    return this.media.collect(gate)
  }

  async collectProcesses(gate: PrivacyGate): Promise<ProcessInfo[]> {
    return (await this.processes.collect(gate)) ?? []
  }

  async collectSystem(gate: PrivacyGate): Promise<SystemInfo | null> {
    return this.system.collect(gate)
  }
}

function buildFilter(config: CollectorConfig): ProcessFilter {
  return new ProcessFilter(config.processWhitelist, undefined, config.processCollectAll)
}

export * from './privacy'
export * from './platform'
export * from './shell'
