import { app, BrowserWindow } from 'electron'
import { existsSync } from 'node:fs'

import { appConfigStore, configPath, platformKey, secretStore, type Language } from './config'
import { logger } from './logger'
import { translator } from './i18n'
import { createAutostartProvider, syncAutostart } from './app/autostart'
import { applyDockPolicy, launchTarget } from './app/runtime'
import { MainWindowController } from './app/main-window'
import { TrayController, type TrayMenuLabels } from './app/tray'

let quitting = false

function trayLabels(language: Language): TrayMenuLabels {
  const t = translator(language)
  return { open: t('menu.open'), quit: t('menu.quit'), status: t('menu.status') }
}

function bootstrap(): void {
  app.setName('HeartBeat')
  if (platformKey() === 'windows') {
    app.setAppUserModelId('com.heartbeat.client')
  }

  app.on('before-quit', () => {
    quitting = true
  })

  app.whenReady().then(() => {
    applyDockPolicy()

    const firstRun = !existsSync(configPath())
    const config = appConfigStore.load()
    secretStore.load()
    logger.info(`Client starting, first_run=${firstRun} platform=${platformKey()}`)

    const provider = createAutostartProvider(launchTarget())
    if (app.isPackaged) {
      const applied = syncAutostart(provider, config.autostart.enabled)
      if (applied !== config.autostart.enabled) {
        appConfigStore.replace({ ...config, autostart: { enabled: applied } })
      }
    } else {
      logger.warn(
        `Autostart left untouched in development, configured=${config.autostart.enabled} registered=${provider.isEnabled()}`
      )
    }

    const windows = new MainWindowController({ isQuitting: () => quitting })
    const tray = new TrayController(trayLabels(config.ui.language), {
      onOpen: () => windows.show(),
      onQuit: () => {
        quitting = true
        app.quit()
      }
    })
    tray.show()

    appConfigStore.subscribe((next) => tray.updateLabels(trayLabels(next.ui.language)))

    const showWindow = firstRun || !config.setup_completed || !config.ui.start_minimized
    if (showWindow) {
      windows.show()
    }

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0 || !windows.instance?.isVisible()) {
        windows.show()
      }
    })

    app.on('will-quit', () => tray.destroy())
  })

  app.on('second-instance', () => {
    app.emit('activate')
  })

  app.on('window-all-closed', () => {
    logger.info('All windows closed, staying resident in the tray')
  })
}

const singleInstance = app.requestSingleInstanceLock()
if (singleInstance) {
  bootstrap()
} else {
  logger.warn('Another instance is already running, exiting')
  app.quit()
}
