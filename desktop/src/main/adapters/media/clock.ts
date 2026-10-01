import { emptyMedia, type MediaInfo } from '../../protocol'

export class MediaClock {
  private trackKey = ''
  private anchorMs = 0
  private anchorMono = Date.now()
  private durationMs = 0

  decorate(info: MediaInfo): MediaInfo {
    const key = trackKeyOf(info)
    const duration = info.duration_ms ?? this.durationMs
    const playing = info.state === 'playing'
    const rawPosition = info.position_ms ?? 0
    const now = Date.now()

    if (key !== this.trackKey) {
      this.trackKey = key
      this.anchorMs = rawPosition
      this.anchorMono = now
    } else if (rawPosition > 0) {
      this.anchorMs = rawPosition
      this.anchorMono = now
    }

    this.durationMs = duration
    let position = rawPosition
    if (position <= 0 && this.trackKey) {
      const elapsed = playing ? now - this.anchorMono : 0
      position = Math.max(this.anchorMs + elapsed, 0)
    }
    if (duration && position > duration) {
      position = duration
    }
    return { ...info, position_ms: position, duration_ms: duration > 0 ? duration : null }
  }

  reset(): void {
    this.trackKey = ''
    this.anchorMs = 0
    this.anchorMono = Date.now()
    this.durationMs = 0
  }
}

function trackKeyOf(info: MediaInfo): string {
  return [info.title ?? '', info.artist ?? '', info.album ?? '', info.app ?? ''].join('|')
}

export function idleMedia(): MediaInfo {
  return emptyMedia()
}
