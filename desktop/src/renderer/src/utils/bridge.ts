import type { HeartbeatBridge } from '@shared/ipc'

export const bridge: HeartbeatBridge = window.heartbeat

export function errorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  return String(error)
}
