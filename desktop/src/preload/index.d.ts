import type { HeartbeatBridge } from './index'

declare global {
  interface Window {
    heartbeat: HeartbeatBridge
  }
}

export {}
