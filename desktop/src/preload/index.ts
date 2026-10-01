import { contextBridge } from 'electron'

const heartbeat = {
  app: {
    platform: process.platform,
    versions: {
      electron: process.versions.electron,
      chrome: process.versions.chrome,
      node: process.versions.node
    }
  }
}

export type HeartbeatBridge = typeof heartbeat

contextBridge.exposeInMainWorld('heartbeat', heartbeat)
