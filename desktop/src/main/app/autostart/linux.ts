import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { homedir } from 'node:os'
import { dirname, join } from 'node:path'

import { logger } from '../../logger'
import { APP_NAME, DESKTOP_FILE_NAME, type AutostartProvider, type AutostartTarget } from './types'

export function desktopEntryPath(): string {
  const base = process.env['XDG_CONFIG_HOME'] ?? join(homedir(), '.config')
  return join(base, 'autostart', DESKTOP_FILE_NAME)
}

export function commandLine(target: AutostartTarget): string {
  return [target.command, ...(target.arguments ?? [])].join(' ')
}

export function buildDesktopEntry(target: AutostartTarget): string {
  return [
    '[Desktop Entry]',
    'Type=Application',
    `Name=${APP_NAME}`,
    `Exec=${commandLine(target)}`,
    'Terminal=false',
    'Hidden=false',
    'X-GNOME-Autostart-enabled=true',
    ''
  ].join('\n')
}

export class LinuxAutostartProvider implements AutostartProvider {
  constructor(private target: AutostartTarget) {}

  enable(): void {
    const path = desktopEntryPath()
    mkdirSync(dirname(path), { recursive: true })
    writeFileSync(path, buildDesktopEntry(this.target), 'utf8')
    logger.info(`Linux autostart enabled: ${path}`)
  }

  disable(): void {
    const path = desktopEntryPath()
    if (!existsSync(path)) {
      return
    }
    const content = readFileSync(path, 'utf8')
    if (content.includes('Hidden=false')) {
      writeFileSync(path, content.replace('Hidden=false', 'Hidden=true'), 'utf8')
    }
    logger.info('Linux autostart disabled')
  }

  isEnabled(): boolean {
    const path = desktopEntryPath()
    if (!existsSync(path)) {
      return false
    }
    return !readFileSync(path, 'utf8').includes('Hidden=true')
  }
}

export function removeDesktopEntry(): void {
  rmSync(desktopEntryPath(), { force: true })
}
