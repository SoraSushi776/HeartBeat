import { existsSync } from 'node:fs'
import { unlink } from 'node:fs/promises'

import { currentPlatform } from './adapters/platform'
import { runCommand } from './adapters/shell'
import { logger } from './logger'

export interface SetupCheckResult {
  id: string
  labelKey: string
  ok: boolean
  detail: string
  actionId: string | null
}

const NOWPLAYING_BINARIES = [
  '/opt/homebrew/bin/nowplaying-cli',
  '/usr/local/bin/nowplaying-cli',
  '/usr/bin/nowplaying-cli'
]

const BREW_BINARIES = ['/opt/homebrew/bin/brew', '/usr/local/bin/brew', '/usr/bin/brew']

const LINUX_CAPTURERS = ['grim', 'gnome-screenshot', 'scrot', 'import']

function findBinary(candidates: string[]): string | null {
  return candidates.find((candidate) => existsSync(candidate)) ?? null
}

async function hasBinary(binary: string): Promise<boolean> {
  const result = await runCommand('/usr/bin/which', [binary], 4000)
  return result.ok && result.stdout.trim().length > 0
}

async function checkNowPlaying(): Promise<SetupCheckResult> {
  const found = findBinary(NOWPLAYING_BINARIES)
  return {
    id: 'nowplaying',
    labelKey: 'setup.nowplaying',
    ok: found !== null,
    detail: found ?? 'not found',
    actionId: found ? null : 'install-nowplaying'
  }
}

async function checkHomebrew(): Promise<SetupCheckResult> {
  const found = findBinary(BREW_BINARIES)
  return {
    id: 'homebrew',
    labelKey: 'setup.homebrew',
    ok: found !== null,
    detail: found ?? 'not found',
    actionId: null
  }
}

async function checkScreenRecording(): Promise<SetupCheckResult> {
  const { systemPreferences } = await import('electron')
  const status = systemPreferences.getMediaAccessStatus('screen')
  return {
    id: 'screen-recording',
    labelKey: 'setup.screen_recording',
    ok: status === 'granted',
    detail: status,
    actionId: status === 'granted' ? null : 'open-screen-recording'
  }
}

async function checkAutomation(): Promise<SetupCheckResult> {
  const result = await runCommand(
    'osascript',
    ['-e', 'tell application "System Events" to return name of first process'],
    6000
  )
  const denied = /-1743|-1728|not authori|未获得授权|不允许/i.test(result.stderr)
  return {
    id: 'automation',
    labelKey: 'setup.automation',
    ok: result.ok && !denied,
    detail: result.ok ? 'granted' : result.stderr.trim().split('\n')[0] || 'denied',
    actionId: result.ok ? null : 'open-automation'
  }
}

async function checkLinuxCapturer(): Promise<SetupCheckResult> {
  const available: string[] = []
  for (const binary of LINUX_CAPTURERS) {
    if (await hasBinary(binary)) {
      available.push(binary)
    }
  }
  return {
    id: 'capture-tool',
    labelKey: 'setup.capture_tool',
    ok: available.length > 0,
    detail: available.join(', ') || 'none found',
    actionId: null
  }
}

export async function runSetupChecks(): Promise<SetupCheckResult[]> {
  const platform = currentPlatform()
  if (platform === 'macos') {
    return [
      await checkHomebrew(),
      await checkNowPlaying(),
      await checkScreenRecording(),
      await checkAutomation()
    ]
  }
  if (platform === 'linux') {
    return [await checkLinuxCapturer()]
  }
  return []
}

export async function runSetupAction(actionId: string): Promise<void> {
  const { shell } = await import('electron')
  if (actionId === 'install-nowplaying') {
    const brew = findBinary(BREW_BINARIES)
    if (!brew) {
      logger.warn('Homebrew missing, cannot install nowplaying-cli')
      return
    }
    const result = await runCommand(brew, ['install', 'nowplaying-cli'], 600000)
    logger.info(`brew install nowplaying-cli ok=${result.ok}`)
    return
  }
  if (actionId === 'open-screen-recording') {
    await shell.openExternal(
      'x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture'
    )
    return
  }
  if (actionId === 'open-automation') {
    await shell.openExternal(
      'x-apple.systempreferences:com.apple.preference.security?Privacy_Automation'
    )
    return
  }
  logger.warn(`Unknown setup action: ${actionId}`)
}

export async function clearTempFile(path: string): Promise<void> {
  try {
    await unlink(path)
  } catch {
    return
  }
}
