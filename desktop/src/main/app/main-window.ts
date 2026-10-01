import { BrowserWindow, app, nativeTheme, shell } from 'electron'
import { join } from 'node:path'

import { logger } from '../logger'
import { windowIconPath } from './assets'

const WINDOW_BOUNDS = { width: 1120, height: 760, minWidth: 920, minHeight: 620 }
const BACKGROUND = { dark: '#111318', light: '#fdf8f6' }

export interface MainWindowOptions {
  isQuitting: () => boolean
}

export class MainWindowController {
  private window: BrowserWindow | null = null

  constructor(private options: MainWindowOptions) {}

  show(): BrowserWindow {
    const window = this.ensure()
    if (window.isMinimized()) {
      window.restore()
    }
    window.show()
    window.focus()
    return window
  }

  hide(): void {
    this.window?.hide()
  }

  toggle(): void {
    if (this.window?.isVisible()) {
      this.hide()
      return
    }
    this.show()
  }

  get instance(): BrowserWindow | null {
    return this.window
  }

  send(channel: string, payload?: unknown): void {
    this.window?.webContents.send(channel, payload)
  }

  private ensure(): BrowserWindow {
    if (this.window && !this.window.isDestroyed()) {
      return this.window
    }
    this.window = this.create()
    return this.window
  }

  private create(): BrowserWindow {
    const window = new BrowserWindow({
      ...WINDOW_BOUNDS,
      show: false,
      title: 'HeartBeat',
      backgroundColor: nativeTheme.shouldUseDarkColors ? BACKGROUND.dark : BACKGROUND.light,
      icon: process.platform === 'darwin' ? undefined : windowIconPath(),
      titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'hidden',
      titleBarOverlay:
        process.platform === 'darwin'
          ? false
          : { color: '#00000000', symbolColor: '#a6a6a6', height: 64 },
      webPreferences: {
        preload: join(__dirname, '../preload/index.js'),
        sandbox: false,
        contextIsolation: true,
        nodeIntegration: false
      }
    })

    window.once('ready-to-show', () => window.show())

    window.on('close', (event) => {
      if (this.options.isQuitting()) {
        return
      }
      event.preventDefault()
      window.hide()
      logger.info('Window hidden to tray')
    })

    window.on('closed', () => {
      this.window = null
    })

    window.webContents.setWindowOpenHandler(({ url }) => {
      void shell.openExternal(url)
      return { action: 'deny' }
    })

    const devServer = process.env['ELECTRON_RENDERER_URL']
    if (!app.isPackaged && devServer) {
      void window.loadURL(devServer)
    } else {
      void window.loadFile(join(__dirname, '../renderer/index.html'))
    }

    logger.info('Main window created')
    return window
  }
}
