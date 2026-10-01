import type { MenuItemConstructorOptions } from 'electron'

export interface TrayMenuLabels {
  open: string
  quit: string
  status: string
}

export interface TrayMenuHandlers {
  onOpen: () => void
  onQuit: () => void
}

export function buildTrayMenuTemplate(
  labels: TrayMenuLabels,
  handlers: TrayMenuHandlers
): MenuItemConstructorOptions[] {
  return [
    { label: labels.status, enabled: false },
    { type: 'separator' },
    { label: labels.open, click: () => handlers.onOpen() },
    { type: 'separator' },
    { label: labels.quit, click: () => handlers.onQuit() }
  ]
}
