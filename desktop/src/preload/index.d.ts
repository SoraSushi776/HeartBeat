import type { HeartbeatBridge } from '../shared/ipc'

declare global {
  interface Window {
    heartbeat: HeartbeatBridge
  }
}

export {}
