import { app } from 'electron'
import { existsSync } from 'node:fs'
import { join } from 'node:path'

import { platformKey } from '../config/paths'

const ICON_BY_PLATFORM = {
  macos: 'icon_tray_mask_256.png',
  windows: 'icon_32.png',
  linux: 'icon_256.png'
} as const

const PROBE_FILE = 'icon.png'

function candidateDirs(): string[] {
  return [
    app.isPackaged ? join(process.resourcesPath, 'icons') : '',
    join(app.getAppPath(), 'resources', 'icons'),
    join(app.getAppPath(), '..', 'resources', 'icons'),
    join(process.cwd(), 'resources', 'icons')
  ].filter((dir) => dir.length > 0)
}

export function iconDir(): string {
  const dirs = candidateDirs()
  return dirs.find((dir) => existsSync(join(dir, PROBE_FILE))) ?? dirs[0]
}

export function trayIconPath(): string {
  return join(iconDir(), ICON_BY_PLATFORM[platformKey()])
}

export function windowIconPath(): string {
  return join(iconDir(), 'icon_256.png')
}

export function isTemplateTrayIcon(): boolean {
  return platformKey() === 'macos'
}
