import { existsSync } from 'node:fs'
import { homedir } from 'node:os'

import { emptyMedia, type MediaInfo } from '../../protocol'
import type { PrivacyGate } from '../privacy'
import { runCommand } from '../shell'
import { MediaClock } from './clock'
import { NowPlayingMediaAdapter } from './nowplaying'
import { preferPlaying, STATE_MAP } from './selection'

const SEPARATOR = '\u001f'
const TIMEOUT_MS = 2000

const MUSIC_SCRIPT = `
if application "Music" is not running then return "idle"
tell application "Music"
set pstate to player state as text
if pstate is "stopped" then return "idle"
set t to name of current track
set a to artist of current track
set al to album of current track
set d to duration of current track
set p to player position
set dms to (d * 1000) as integer
set pms to (p * 1000) as integer
set sep to (ASCII character 31)
return pstate & sep & t & sep & a & sep & al & sep & (dms as text) & sep & (pms as text)
end tell
`

const SPOTIFY_SCRIPT = `
if application "Spotify" is not running then return "idle"
tell application "Spotify"
set pstate to player state as text
if pstate is "stopped" then return "idle"
set t to name of current track
set a to artist of current track
set al to album of current track
set d to duration of current track
set pms to (player position * 1000) as integer
set art to artwork url of current track
set sep to (ASCII character 31)
return pstate & sep & t & sep & a & sep & al & sep & (d as text) & sep & (pms as text) & sep & art
end tell
`

export const APP_SCRIPTS: Array<{ app: string; script: string; bundles: string[] }> = [
  {
    app: 'Music',
    script: MUSIC_SCRIPT,
    bundles: ['/System/Applications/Music.app', '/Applications/Music.app']
  },
  {
    app: 'Spotify',
    script: SPOTIFY_SCRIPT,
    bundles: ['/Applications/Spotify.app', `${homedir()}/Applications/Spotify.app`]
  }
]

export function installedAppScripts(): Array<{ app: string; script: string }> {
  return APP_SCRIPTS.filter((entry) => entry.bundles.some((bundle) => existsSync(bundle))).map(
    (entry) => ({ app: entry.app, script: entry.script })
  )
}

function asMs(raw: string): number | null {
  const value = raw.trim()
  if (!value) {
    return null
  }
  const parsed = Number.parseFloat(value)
  return Number.isFinite(parsed) ? Math.round(parsed) : null
}

export function parseScriptOutput(raw: string, app: string): MediaInfo {
  const text = raw.trim()
  if (!text || text === 'idle') {
    return emptyMedia()
  }
  const parts = text.split(SEPARATOR)
  if (parts.length < 6) {
    return emptyMedia()
  }
  return {
    state: STATE_MAP[parts[0].trim().toLowerCase()] ?? 'idle',
    title: parts[1] || null,
    artist: parts[2] || null,
    album: parts[3] || null,
    app,
    cover_url: parts.length > 6 && parts[6] ? parts[6] : null,
    cover_bytes: null,
    duration_ms: asMs(parts[4]),
    position_ms: asMs(parts[5])
  }
}

export class MacosMediaAdapter {
  private nowPlaying = new NowPlayingMediaAdapter()
  private clock = new MediaClock()

  async collect(gate: PrivacyGate): Promise<MediaInfo | null> {
    if (!gate.allow('media')) {
      return null
    }
    const candidates: MediaInfo[] = []
    const viaNowPlaying = await this.nowPlaying.collect(gate)
    if (viaNowPlaying) {
      candidates.push(viaNowPlaying)
    }
    for (const entry of installedAppScripts()) {
      candidates.push(await this.query(entry.app, entry.script))
    }
    return this.clock.decorate(preferPlaying(candidates))
  }

  private async query(app: string, script: string): Promise<MediaInfo> {
    const result = await runCommand('osascript', ['-e', script], TIMEOUT_MS)
    return parseScriptOutput(result.ok ? result.stdout : '', app)
  }
}
