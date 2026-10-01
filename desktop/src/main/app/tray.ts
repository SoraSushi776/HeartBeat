import { Menu, Tray, nativeImage } from 'electron'

import { logger } from '../logger'
import { platformKey } from '../config/paths'
import { isTemplateTrayIcon, trayIconPath } from './assets'
import { buildTrayMenuTemplate, type TrayMenuHandlers, type TrayMenuLabels } from './tray-menu'

export class TrayController {
  private tray: Tray | null = null
  private menu: Menu | null = null

  constructor(
    private labels: TrayMenuLabels,
    private handlers: TrayMenuHandlers
  ) {}

  show(): void {
    if (this.tray) {
      return
    }
    const image = nativeImage.createFromPath(trayIconPath())
    if (isTemplateTrayIcon()) {
      image.setTemplateImage(true)
    }
    this.tray = new Tray(image)
    this.tray.setToolTip('HeartBeat')
    this.rebuildMenu()
    if (platformKey() !== 'macos') {
      this.tray.setContextMenu(this.menu)
    }
    const restore = (): void => this.handlers.onOpen()
    this.tray.on('click', restore)
    this.tray.on('double-click', restore)
    this.tray.on('middle-click', restore)
    this.tray.on('right-click', () => {
      if (platformKey() === 'macos' && this.menu) {
        this.tray?.popUpContextMenu(this.menu)
      }
    })
    logger.info(`Tray shown, icon=${trayIconPath()}`)
  }

  updateLabels(labels: TrayMenuLabels): void {
    this.labels = labels
    if (!this.tray) {
      return
    }
    this.rebuildMenu()
    if (platformKey() !== 'macos') {
      this.tray.setContextMenu(this.menu)
    }
  }

  destroy(): void {
    this.tray?.destroy()
    this.tray = null
    this.menu = null
  }

  private rebuildMenu(): void {
    this.menu = Menu.buildFromTemplate(buildTrayMenuTemplate(this.labels, this.handlers))
  }
}

export type { TrayMenuHandlers, TrayMenuLabels }
