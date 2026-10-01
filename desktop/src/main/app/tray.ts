import { Menu, Tray, nativeImage } from 'electron'

import { logger } from '../logger'
import { platformKey } from '../config/paths'
import { isTemplateTrayIcon, trayIconPath } from './assets'
import { buildTrayMenuTemplate, type TrayMenuHandlers, type TrayMenuLabels } from './tray-menu'

const TRAY_ICON_PT = { macos: 16, windows: 16, linux: 22 } as const

function loadTrayImage(): Electron.NativeImage {
  const source = nativeImage.createFromPath(trayIconPath())
  if (source.isEmpty()) {
    return source
  }
  const size = TRAY_ICON_PT[platformKey()]
  const image = source.resize({ width: size, height: size })
  image.addRepresentation({
    scaleFactor: 2,
    buffer: source.resize({ width: size * 2, height: size * 2 }).toPNG()
  })
  if (isTemplateTrayIcon()) {
    image.setTemplateImage(true)
  }
  return image
}

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
    const image = loadTrayImage()
    if (image.isEmpty()) {
      logger.warn(`Tray icon is empty at ${trayIconPath()}`)
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
    logger.info(
      `Tray shown icon=${trayIconPath()} size=${image.getSize().width}x${image.getSize().height} template=${image.isTemplateImage()}`
    )
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
