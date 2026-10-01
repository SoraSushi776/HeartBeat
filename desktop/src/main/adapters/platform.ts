import type { Platform } from '../protocol'

const KEY_BY_PLATFORM: Partial<Record<NodeJS.Platform, Platform>> = {
  darwin: 'macos',
  win32: 'windows',
  linux: 'linux'
}

export function currentPlatform(): Platform {
  const key = KEY_BY_PLATFORM[process.platform]
  if (!key) {
    throw new Error(`unsupported platform: ${process.platform}`)
  }
  return key
}

export function isUnix(): boolean {
  return currentPlatform() !== 'windows'
}
