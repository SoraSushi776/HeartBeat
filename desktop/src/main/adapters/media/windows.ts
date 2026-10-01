import { logger } from '../../logger'
import { emptyMedia, type MediaInfo, type MediaState } from '../../protocol'
import type { PrivacyGate } from '../privacy'
import { runCommand } from '../shell'
import { MediaClock } from './clock'
import { STATE_MAP, preferPlaying } from './selection'

const TIMEOUT_MS = 6000

const APP_NAME_MAP: Record<string, string> = {
  'Microsoft.ZuneMusic_8wekyb3d8bbwe!Microsoft.ZuneMusic': 'Media Player',
  'Microsoft.Media.Player_8wekyb3d8bbwe!Microsoft.Media.Player': 'Media Player',
  'Spotify.exe': 'Spotify',
  'SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify': 'Spotify',
  'Chrome.exe': 'Chrome',
  'msedge.exe': 'Edge'
}

const SESSION_SCRIPT = `
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime | Out-Null
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation\`1' })[0]
function Await($operation, $type) {
  $asTask = $asTaskGeneric.MakeGenericMethod($type)
  $task = $asTask.Invoke($null, @($operation))
  $task.Wait(-1) | Out-Null
  $task.Result
}
[Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media.Control, ContentType = WindowsRuntime] | Out-Null
[Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties, Windows.Media.Control, ContentType = WindowsRuntime] | Out-Null
$manager = Await ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync()) ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager])
$sessions = @()
$current = $manager.GetCurrentSession()
if ($null -ne $current) { $sessions += $current }
$sessions += @($manager.GetSessions())
$rows = @()
foreach ($session in $sessions) {
  if ($null -eq $session) { continue }
  try {
    $props = Await ($session.TryGetMediaPropertiesAsync()) ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties])
    $playback = $session.GetPlaybackInfo()
    $timeline = $session.GetTimelineProperties()
    $rows += [pscustomobject]@{
      app = $session.SourceAppUserModelId
      status = $playback.PlaybackStatus.ToString()
      title = $props.Title
      artist = $props.Artist
      album = $props.AlbumTitle
      positionMs = [int]$timeline.Position.TotalMilliseconds
      endMs = [int]$timeline.EndTime.TotalMilliseconds
    }
  } catch { }
}
if ($rows.Count -eq 0) { Write-Output '[]' } else { Write-Output ($rows | ConvertTo-Json -Compress -Depth 4) }
`

export function encodePowerShell(script: string): string {
  return Buffer.from(script, 'utf16le').toString('base64')
}

export function friendlyAppName(appId: string): string | null {
  if (!appId) {
    return null
  }
  return APP_NAME_MAP[appId] ?? (appId.split('!')[0] || null)
}

interface SessionRow {
  app?: string
  status?: string
  title?: string
  artist?: string
  album?: string
  positionMs?: number
  endMs?: number
}

export function parseSessions(raw: string): MediaInfo[] {
  const text = raw.trim()
  if (!text) {
    return []
  }
  let parsed: unknown
  try {
    parsed = JSON.parse(text)
  } catch {
    logger.debug('Invalid GSMTC json')
    return []
  }
  const rows = Array.isArray(parsed) ? parsed : [parsed]
  const results: MediaInfo[] = []
  for (const row of rows) {
    if (typeof row !== 'object' || row === null) {
      continue
    }
    const item = row as SessionRow
    const state: MediaState = STATE_MAP[(item.status ?? '').toLowerCase()] ?? 'idle'
    const title = (item.title ?? '').trim() || null
    if (state === 'idle' && !title) {
      continue
    }
    results.push({
      state,
      title,
      artist: (item.artist ?? '').trim() || null,
      album: (item.album ?? '').trim() || null,
      app: friendlyAppName((item.app ?? '').trim()),
      cover_url: null,
      cover_bytes: null,
      position_ms: typeof item.positionMs === 'number' ? item.positionMs : null,
      duration_ms: typeof item.endMs === 'number' && item.endMs > 0 ? item.endMs : null
    })
  }
  return results
}

export class WindowsMediaAdapter {
  private clock = new MediaClock()

  async collect(gate: PrivacyGate): Promise<MediaInfo | null> {
    if (!gate.allow('media')) {
      return null
    }
    const result = await runCommand(
      'powershell',
      ['-NoProfile', '-NonInteractive', '-EncodedCommand', encodePowerShell(SESSION_SCRIPT)],
      TIMEOUT_MS
    )
    if (!result.ok) {
      logger.debug('GSMTC query failed')
      return emptyMedia()
    }
    return this.clock.decorate(preferPlaying(parseSessions(result.stdout)))
  }
}
