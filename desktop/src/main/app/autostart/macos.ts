import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, rmSync, writeFileSync } from 'node:fs'
import { homedir } from 'node:os'
import { dirname, join } from 'node:path'

import { logger } from '../../logger'
import { APP_LABEL, PLIST_NAME, type AutostartProvider, type AutostartTarget } from './types'

const PROLOGUE = [
  '<?xml version="1.0" encoding="UTF-8"?>',
  '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">',
  '<plist version="1.0">'
].join('\n')

function xmlEscape(value: string): string {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;')
}

export function plistPath(): string {
  return join(homedir(), 'Library', 'LaunchAgents', PLIST_NAME)
}

export function buildPlist(target: AutostartTarget): string {
  const programArguments = [target.command, ...(target.arguments ?? [])]
  const entries = [
    '\t<key>Label</key>',
    `\t<string>${xmlEscape(APP_LABEL)}</string>`,
    '\t<key>ProgramArguments</key>',
    '\t<array>',
    ...programArguments.map((item) => `\t\t<string>${xmlEscape(item)}</string>`),
    '\t</array>',
    ...(target.workingDirectory
      ? ['\t<key>WorkingDirectory</key>', `\t<string>${xmlEscape(target.workingDirectory)}</string>`]
      : []),
    '\t<key>RunAtLoad</key>',
    '\t<true/>',
    '\t<key>ProcessType</key>',
    '\t<string>Interactive</string>'
  ]
  return `${PROLOGUE}\n<dict>\n${entries.join('\n')}\n</dict>\n</plist>\n`
}

export function launchctlArgs(action: 'bootstrap' | 'bootout', target: string): string[] {
  return [action, `gui/${process.getuid?.() ?? 0}`, target]
}

function runLaunchctl(args: string[]): void {
  try {
    execFileSync('launchctl', args, { stdio: 'pipe' })
  } catch (error) {
    logger.warn(`launchctl ${args[0]} failed: ${String(error)}`)
  }
}

export class MacosAutostartProvider implements AutostartProvider {
  constructor(private target: AutostartTarget) {}

  enable(): void {
    const path = plistPath()
    mkdirSync(dirname(path), { recursive: true })
    writeFileSync(path, buildPlist(this.target), 'utf8')
    runLaunchctl(launchctlArgs('bootout', path))
    runLaunchctl(launchctlArgs('bootstrap', path))
    logger.info(`macOS autostart enabled: ${path}`)
  }

  disable(): void {
    const path = plistPath()
    runLaunchctl(launchctlArgs('bootout', path))
    rmSync(path, { force: true })
    logger.info('macOS autostart disabled')
  }

  isEnabled(): boolean {
    return existsSync(plistPath())
  }
}
