import { platformKey, type PlatformKey } from '../../config/paths'
import { LinuxAutostartProvider } from './linux'
import { MacosAutostartProvider } from './macos'
import { WindowsAutostartProvider } from './windows'
import type { AutostartProvider, AutostartTarget } from './types'

type ProviderFactory = (target: AutostartTarget) => AutostartProvider

const PROVIDERS: Record<PlatformKey, ProviderFactory> = {
  macos: (target) => new MacosAutostartProvider(target),
  windows: (target) => new WindowsAutostartProvider(target),
  linux: (target) => new LinuxAutostartProvider(target)
}

export function createAutostartProvider(target: AutostartTarget): AutostartProvider {
  return PROVIDERS[platformKey()](target)
}

export function syncAutostart(provider: AutostartProvider, enabled: boolean): boolean {
  if (!enabled) {
    if (provider.isEnabled()) {
      provider.disable()
    }
    return provider.isEnabled()
  }
  if (!provider.isEnabled() || !provider.isUpToDate()) {
    provider.enable()
  }
  return provider.isEnabled()
}

export * from './types'
