import { emptyMedia, type MediaInfo, type MediaState } from '../../protocol'

const STATE_RANK: Record<MediaState, number> = { playing: 2, paused: 1, idle: 0 }

export const STATE_MAP: Record<string, MediaState> = {
  playing: 'playing',
  paused: 'paused',
  stopped: 'idle',
  idle: 'idle',
  closed: 'idle',
  opened: 'idle',
  changing: 'paused'
}

export function preferPlaying(candidates: MediaInfo[]): MediaInfo {
  let best = emptyMedia()
  for (const candidate of candidates) {
    if (STATE_RANK[candidate.state] > STATE_RANK[best.state]) {
      best = candidate
    }
  }
  return best
}
