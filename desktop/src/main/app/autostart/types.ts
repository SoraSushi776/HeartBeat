export interface AutostartProvider {
  enable: () => void
  disable: () => void
  isEnabled: () => boolean
}

export interface AutostartTarget {
  command: string
  arguments?: string[]
  workingDirectory?: string
}

export const APP_LABEL = 'com.heartbeat.client'
export const APP_NAME = 'HeartBeat'
export const PLIST_NAME = `${APP_LABEL}.plist`
export const DESKTOP_FILE_NAME = 'heartbeat-client.desktop'
