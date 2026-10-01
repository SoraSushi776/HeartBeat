import { app } from 'electron'

import { platformKey } from '../config/paths'
import { logger } from '../logger'
import type { AutostartTarget } from './autostart'

type DockPolicy = 'accessory' | 'regular'

const POLICY_BY_PLATFORM: Partial<Record<ReturnType<typeof platformKey>, DockPolicy>> = {
  macos: 'accessory'
}

export function applyDockPolicy(): void {
  const policy = POLICY_BY_PLATFORM[platformKey()]
  if (!policy) {
    return
  }
  app.setActivationPolicy(policy)
  logger.info(`macOS activation policy set to ${policy}`)
}

export function launchTarget(): AutostartTarget {
  if (app.isPackaged) {
    return { command: process.execPath, workingDirectory: app.getAppPath() }
  }
  return {
    command: process.execPath,
    arguments: [app.getAppPath()],
    workingDirectory: app.getAppPath()
  }
}
