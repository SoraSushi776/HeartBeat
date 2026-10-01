import { existsSync } from 'node:fs'

import { logger } from '../../logger'
import { emptyMedia, type MediaInfo, type MediaState } from '../../protocol'
import type { PrivacyGate } from '../privacy'
import { runCommand } from '../shell'

const BINARY_CANDIDATES = [
  'nowplaying-cli',
  '/opt/homebrew/bin/nowplaying-cli',
  '/usr/local/bin/nowplaying-cli'
]

const TIMEOUT_MS = 2000

const APP_NAME_BY_BUNDLE: Record<string, string> = {
  'top.imsyy.splayer-next': 'SPlayer',
  'com.apple.Music': 'Music',
  'com.spotify.client': 'Spotify'
}

export function resolveNowPlayingBinary(): string | null {
  for (const candidate of BINARY_CANDIDATES) {
    if (candidate.includes('/') && existsSync(candidate)) {
      return candidate
    }
  }
  return null
}

export function parseNowPlayingJson(raw: string): MediaInfo {
  const text = raw.trim()
  if (!text) {
    return emptyMedia()
  }
  let data: Record<string, unknown>
  try {
    const parsed = JSON.parse(text) as unknown
    if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
      return emptyMedia()
    }
    data = parsed as Record<string, unknown>
  } catch {
    logger.debug('Invalid nowplaying json')
    return emptyMedia()
  }
  const title = asText(data['title'])
  const artist = asText(data['artist'])
  if (!title && !artist) {
    return emptyMedia()
  }
  const rate = data['playbackRate']
  const playing = typeof rate === 'number' && rate > 0
  const rateIsSet = typeof rate === 'number' ? rate !== 0 : Boolean(rate)
  const state: MediaState = playing ? 'playing' : rateIsSet ? 'paused' : 'idle'
  return {
    state,
    title,
    artist,
    album: asText(data['album']),
    app: appName(data['clientBundleIdentifier']),
    cover_url: null,
    cover_bytes: artworkBytes(data['artworkData']),
    duration_ms: secondsToMs(data['duration']),
    position_ms: secondsToMs(data['elapsedTime'])
  }
}

function asText(value: unknown): string | null {
  if (typeof value === 'string' && value.trim()) {
    return value.trim()
  }
  return null
}

function appName(bundle: unknown): string | null {
  const text = asText(bundle)
  if (!text) {
    return null
  }
  return APP_NAME_BY_BUNDLE[text] ?? (text.split('.').pop() || text)
}

function secondsToMs(value: unknown): number | null {
  return typeof value === 'number' ? Math.round(value * 1000) : null
}

function artworkBytes(value: unknown): Buffer | null {
  const text = asText(value)
  if (!text) {
    return null
  }
  const buffer = Buffer.from(text, 'base64')
  return buffer.length > 0 ? buffer : null
}

export class NowPlayingMediaAdapter {
  private binary: string | null

  constructor(binary: string | null = resolveNowPlayingBinary()) {
    this.binary = binary
  }

  get available(): boolean {
    return this.binary !== null
  }

  async collect(gate: PrivacyGate): Promise<MediaInfo | null> {
    if (!gate.allow('media')) {
      return null
    }
    if (!this.binary) {
      return emptyMedia()
    }
    const result = await runCommand(
      this.binary,
      [
        'get',
        '--json',
        'title',
        'artist',
        'album',
        'elapsedTime',
        'duration',
        'playbackRate',
        'clientBundleIdentifier',
        'artworkData'
      ],
      TIMEOUT_MS
    )
    return parseNowPlayingJson(result.ok ? result.stdout : '')
  }
}
