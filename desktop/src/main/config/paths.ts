import { homedir } from 'node:os'
import { join } from 'node:path'

export type PlatformKey = 'macos' | 'windows' | 'linux'

export const APP_DIR_NAME = 'HeartBeat'
export const LINUX_DIR_NAME = 'heartbeat'
export const CONFIG_FILE_NAME = 'client.json'
export const SECRETS_FILE_NAME = 'client.secrets.json'

const KEY_BY_PLATFORM: Partial<Record<NodeJS.Platform, PlatformKey>> = {
  darwin: 'macos',
  win32: 'windows',
  linux: 'linux'
}

const DIR_BUILDERS: Record<PlatformKey, () => string> = {
  macos: () => join(homedir(), 'Library', 'Application Support', APP_DIR_NAME),
  windows: () => join(process.env['APPDATA'] ?? join(homedir(), 'AppData', 'Roaming'), APP_DIR_NAME),
  linux: () => join(process.env['XDG_CONFIG_HOME'] ?? join(homedir(), '.config'), LINUX_DIR_NAME)
}

export function platformKey(): PlatformKey {
  return KEY_BY_PLATFORM[process.platform] ?? 'linux'
}

export function configDir(): string {
  return DIR_BUILDERS[platformKey()]()
}

export function configPath(): string {
  return join(configDir(), CONFIG_FILE_NAME)
}

export function secretsPath(): string {
  return join(configDir(), SECRETS_FILE_NAME)
}
