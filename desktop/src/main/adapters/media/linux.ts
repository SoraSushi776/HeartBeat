import dbus from 'dbus-next'

import { logger } from '../../logger'
import { emptyMedia, type MediaInfo } from '../../protocol'
import type { PrivacyGate } from '../privacy'
import { STATE_MAP, preferPlaying } from './selection'

const PLAYER_PREFIX = 'org.mpris.MediaPlayer2.'
const OBJECT_PATH = '/org/mpris/MediaPlayer2'
const PLAYER_INTERFACE = 'org.mpris.MediaPlayer2.Player'
const PROPERTIES_INTERFACE = 'org.freedesktop.DBus.Properties'
const DBUS_NAME = 'org.freedesktop.DBus'
const DBUS_PATH = '/org/freedesktop/DBus'
const TIMEOUT_MS = 3000

function isVariant(value: unknown): value is { signature: string; value: unknown } {
  return (
    typeof value === 'object' &&
    value !== null &&
    'signature' in value &&
    'value' in value &&
    typeof (value as { signature: unknown }).signature === 'string'
  )
}

export function unwrap(value: unknown): unknown {
  let current = value
  let guard = 0
  while (isVariant(current) && guard < 8) {
    current = current.value
    guard += 1
  }
  return current
}

function asText(value: unknown): string | null {
  const raw = unwrap(value)
  if (raw === null || raw === undefined) {
    return null
  }
  const text = String(raw).trim()
  return text || null
}

function asArtist(value: unknown): string | null {
  const raw = unwrap(value)
  if (Array.isArray(raw)) {
    const joined = raw.map((item) => String(unwrap(item))).join(', ').trim()
    return joined || null
  }
  return asText(raw)
}

function usToMs(value: unknown): number | null {
  const raw = unwrap(value)
  const parsed = typeof raw === 'number' ? raw : Number.parseInt(String(raw), 10)
  return Number.isFinite(parsed) ? Math.round(parsed / 1000) : null
}

export function parseMetadata(
  metadata: Record<string, unknown>,
  status: string,
  app: string,
  positionUs: unknown = null
): MediaInfo {
  return {
    state: STATE_MAP[status.trim().toLowerCase()] ?? 'idle',
    title: asText(metadata['xesam:title']),
    artist: asArtist(metadata['xesam:artist']),
    album: asText(metadata['xesam:album']),
    app,
    cover_url: asText(metadata['mpris:artUrl']),
    cover_bytes: null,
    duration_ms: usToMs(metadata['mpris:length']),
    position_ms: usToMs(positionUs ?? metadata['mpris:position'])
  }
}

export function playerNameFromBusName(busName: string): string {
  return busName.startsWith(PLAYER_PREFIX) ? busName.slice(PLAYER_PREFIX.length) : busName
}

function withTimeout<T>(promise: Promise<T>, fallback: T): Promise<T> {
  return Promise.race([
    promise,
    new Promise<T>((resolve) => {
      setTimeout(() => resolve(fallback), TIMEOUT_MS).unref()
    })
  ])
}

export class LinuxMediaAdapter {
  async collect(gate: PrivacyGate): Promise<MediaInfo | null> {
    if (!gate.allow('media')) {
      return null
    }
    let bus: ReturnType<typeof dbus.sessionBus> | null = null
    try {
      bus = dbus.sessionBus()
      const candidates = await this.queryPlayers(bus)
      return preferPlaying(candidates)
    } catch (error) {
      logger.debug(`MPRIS query failed: ${String(error)}`)
      return emptyMedia()
    } finally {
      bus?.disconnect()
    }
  }

  private async queryPlayers(bus: ReturnType<typeof dbus.sessionBus>): Promise<MediaInfo[]> {
    const busObject = await bus.getProxyObject(DBUS_NAME, DBUS_PATH)
    const dbusInterface = busObject.getInterface(DBUS_NAME)
    const names = (await withTimeout(
      dbusInterface.ListNames() as Promise<string[]>,
      [] as string[]
    )).filter((name) => name.startsWith(PLAYER_PREFIX))

    const found: MediaInfo[] = []
    for (const name of names) {
      const info = await this.readPlayer(bus, name)
      if (info) {
        found.push(info)
      }
    }
    return found
  }

  private async readPlayer(
    bus: ReturnType<typeof dbus.sessionBus>,
    busName: string
  ): Promise<MediaInfo | null> {
    try {
      const object = await bus.getProxyObject(busName, OBJECT_PATH)
      const properties = object.getInterface(PROPERTIES_INTERFACE)
      const all = (await withTimeout(
        properties.GetAll(PLAYER_INTERFACE) as Promise<Record<string, unknown>>,
        {}
      )) as Record<string, unknown>
      const metadata = unwrap(all['Metadata'])
      if (typeof metadata !== 'object' || metadata === null) {
        return null
      }
      const status = String(unwrap(all['PlaybackStatus']) ?? 'Stopped')
      const info = parseMetadata(
        metadata as Record<string, unknown>,
        status,
        playerNameFromBusName(busName),
        all['Position']
      )
      return info.state === 'idle' ? null : info
    } catch (error) {
      logger.debug(`MPRIS player ${busName} failed: ${String(error)}`)
      return null
    }
  }
}
