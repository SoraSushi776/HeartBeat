import { fetchStatus } from "./http"
import type { SnapshotEvent, StatusData } from "../types/protocol"

export type StreamMode = "sse" | "poll" | "idle"

export interface StreamHandlers {
  onStatus: (data: StatusData) => void
  onSnapshot: (data: SnapshotEvent) => void
  onModeChange: (mode: StreamMode) => void
}

const POLL_MS = 15000

export class StatusStream {
  private source: EventSource | null = null
  private timer: number | null = null
  private closed = false

  constructor(private readonly handlers: StreamHandlers) {}

  /** 启动 SSE，失败或不可用时降级为 15 秒轮询 */
  start(): void {
    this.closed = false
    if (typeof EventSource === "undefined") {
      this.startPolling()
      return
    }
    this.handlers.onModeChange("sse")
    const source = new EventSource("/api/v1/stream")
    this.source = source
    source.addEventListener("status", (event) => this.emitStatus(event))
    source.addEventListener("heartbeat", (event) => this.emitStatus(event))
    source.addEventListener("snapshot", (event) => this.emitSnapshot(event))
    source.onerror = () => {
      source.close()
      this.source = null
      if (!this.closed) {
        this.startPolling()
      }
    }
  }

  /** 断开 SSE 与轮询定时器 */
  stop(): void {
    this.closed = true
    this.source?.close()
    this.source = null
    if (this.timer !== null) {
      window.clearInterval(this.timer)
      this.timer = null
    }
    this.handlers.onModeChange("idle")
  }

  private startPolling(): void {
    if (this.timer !== null) {
      return
    }
    this.handlers.onModeChange("poll")
    void this.pollOnce()
    this.timer = window.setInterval(() => void this.pollOnce(), POLL_MS)
  }

  private async pollOnce(): Promise<void> {
    try {
      this.handlers.onStatus(await fetchStatus())
    } catch {
      return
    }
  }

  private emitStatus(event: MessageEvent<string>): void {
    try {
      this.handlers.onStatus(JSON.parse(event.data) as StatusData)
    } catch {
      return
    }
  }

  private emitSnapshot(event: MessageEvent<string>): void {
    try {
      this.handlers.onSnapshot(JSON.parse(event.data) as SnapshotEvent)
    } catch {
      return
    }
  }
}
