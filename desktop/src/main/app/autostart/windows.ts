import { execFileSync } from 'node:child_process'

import { logger } from '../../logger'
import { APP_NAME, type AutostartProvider, type AutostartTarget } from './types'

export const RUN_KEY = 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run'

export function quoteCommand(command: string): string {
  return /\s/.test(command) ? `"${command}"` : command
}

export function commandLine(target: AutostartTarget): string {
  return [target.command, ...(target.arguments ?? [])].map(quoteCommand).join(' ')
}

export function registryAddArgs(target: AutostartTarget): string[] {
  return [
    'add',
    RUN_KEY,
    '/v',
    APP_NAME,
    '/t',
    'REG_SZ',
    '/d',
    commandLine(target),
    '/f'
  ]
}

export function registryDeleteArgs(): string[] {
  return ['delete', RUN_KEY, '/v', APP_NAME, '/f']
}

export function registryQueryArgs(): string[] {
  return ['query', RUN_KEY, '/v', APP_NAME]
}

function runReg(args: string[]): { ok: boolean; output: string } {
  try {
    const output = execFileSync('reg', args, { stdio: 'pipe', encoding: 'utf8' })
    return { ok: true, output }
  } catch (error) {
    return { ok: false, output: String(error) }
  }
}

export class WindowsAutostartProvider implements AutostartProvider {
  constructor(private target: AutostartTarget) {}

  enable(): void {
    const result = runReg(registryAddArgs(this.target))
    logger.info(`Windows autostart ${result.ok ? 'enabled' : 'failed'}`)
  }

  disable(): void {
    const result = runReg(registryDeleteArgs())
    logger.info(`Windows autostart disabled, ok=${result.ok}`)
  }

  isEnabled(): boolean {
    return runReg(registryQueryArgs()).ok
  }

  isUpToDate(): boolean {
    const result = runReg(registryQueryArgs())
    if (!result.ok) {
      return false
    }
    return parseRegistryValue(result.output) === commandLine(this.target)
  }
}

export function parseRegistryValue(output: string): string {
  const match = /REG_SZ\s+(.+)$/m.exec(output.trim())
  return match ? match[1].trim() : ''
}
