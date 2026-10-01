import { BrowserWindow, app, dialog, ipcMain } from 'electron'
import { readFile } from 'node:fs/promises'

import { appConfigStore, configPath, secretsPath, secretStore, type AppConfig, type Secrets } from './config'
import { logger } from './logger'
import { toBackgroundJpeg } from './imaging'
import { runSetupAction, runSetupChecks } from './setup'
import type { CollectorHost } from './collector-host'
import type { DiagnosticsSnapshot } from './collector'
import {
  IPC,
  type AppInfo,
  type BackgroundUploadResult,
  type BanItem,
  type ConfigBundle,
  type DiaryItem,
  type DiaryList,
  type FriendItem,
  type MessageItem,
  type MessageList,
  type SaveResult,
  type SetupReport,
  type SnapshotView
} from '../shared/ipc'

export interface IpcContext {
  host: CollectorHost
  isQuitting: () => boolean
}

function bundle(config: AppConfig, secrets: Secrets): ConfigBundle {
  return {
    config,
    secrets,
    configPath: configPath(),
    secretsPath: secretsPath(),
    clientVersion: app.getVersion()
  }
}

function asList<T>(value: unknown, key = 'items'): T[] {
  if (Array.isArray(value)) {
    return value as T[]
  }
  if (value && typeof value === 'object') {
    const nested = (value as Record<string, unknown>)[key]
    if (Array.isArray(nested)) {
      return nested as T[]
    }
  }
  return []
}

export function registerIpc(context: IpcContext): void {
  const { host } = context

  const api = (): CollectorHost['apiService'] => host.apiService

  ipcMain.handle(IPC.appInfo, (): AppInfo => ({
    platform: process.platform,
    version: app.getVersion(),
    electron: process.versions.electron,
    chrome: process.versions.chrome,
    node: process.versions.node
  }))

  ipcMain.handle(IPC.windowHide, (event): void => {
    BrowserWindow.fromWebContents(event.sender)?.hide()
  })

  ipcMain.handle(IPC.windowShow, (event): void => {
    BrowserWindow.fromWebContents(event.sender)?.show()
  })

  ipcMain.handle(IPC.configLoad, (): ConfigBundle => bundle(appConfigStore.get(), secretStore.get()))

  ipcMain.handle(IPC.configSave, async (_event, incoming: ConfigBundle): Promise<SaveResult> => {
    const pushWarnings: string[] = []
    const config = appConfigStore.replace(incoming.config)
    const secrets = secretStore.replace(incoming.secrets)
    try {
      await api().setGithubToken(secrets.github_token, secrets.github_login)
    } catch (error) {
      pushWarnings.push(`github: ${String(error)}`)
      logger.warn(`GitHub token push failed: ${String(error)}`)
    }
    try {
      await api().updateSite(sitePayload(config))
    } catch (error) {
      pushWarnings.push(`site: ${String(error)}`)
      logger.warn(`Site push failed: ${String(error)}`)
    }
    return { bundle: bundle(config, secrets), pushWarnings }
  })

  ipcMain.handle(IPC.diagnosticsSnapshot, async (): Promise<SnapshotView> => {
    const collector = host.collectorInstance
    if (!collector) {
      return { media: null, coverDataUrl: null, system: null, collectedAt: Date.now() }
    }
    return toSnapshotView(await collector.collectDiagnostics())
  })

  ipcMain.handle(IPC.diagnosticsHistory, () => host.history)

  ipcMain.handle(IPC.setupReport, async (): Promise<SetupReport> => ({ checks: await runSetupChecks() }))

  ipcMain.handle(IPC.setupAction, async (_event, actionId: string): Promise<SetupReport> => {
    await runSetupAction(actionId)
    return { checks: await runSetupChecks() }
  })

  ipcMain.handle(IPC.diaryList, async (): Promise<DiaryList> => {
    const data = await api().listDiaries()
    return {
      items: asList<DiaryItem>(data),
      total: total(data, asList<DiaryItem>(data).length),
      limit: 50,
      offset: 0
    }
  })

  ipcMain.handle(IPC.diaryCreate, async (_event, payload: Partial<DiaryItem>) => api().createDiary(diaryPayload(payload)))
  ipcMain.handle(IPC.diaryUpdate, async (_event, id: number, payload: Partial<DiaryItem>) => api().updateDiary(id, diaryPayload(payload)))
  ipcMain.handle(IPC.diaryDelete, async (_event, id: number) => api().deleteDiary(id))

  ipcMain.handle(IPC.friendList, async (): Promise<FriendItem[]> => asList<FriendItem>(await api().listFriends()))
  ipcMain.handle(IPC.friendCreate, async (_event, payload: Partial<FriendItem>) => api().createFriend(friendPayload(payload)))
  ipcMain.handle(IPC.friendUpdate, async (_event, id: number, payload: Partial<FriendItem>) => api().updateFriend(id, friendPayload(payload)))
  ipcMain.handle(IPC.friendDelete, async (_event, id: number) => api().deleteFriend(id))

  ipcMain.handle(IPC.messageList, async (): Promise<MessageList> => {
    const data = await api().listMessages(50, 0)
    const items = asList<MessageItem>(data)
    return { items, total: total(data, items.length), limit: 50, offset: 0 }
  })
  ipcMain.handle(IPC.messageDelete, async (_event, id: number) => api().deleteMessage(id))
  ipcMain.handle(IPC.messageReply, async (_event, id: number, content: string) => api().createMessageReply(id, content))

  ipcMain.handle(IPC.banList, async (): Promise<BanItem[]> => asList<BanItem>(await api().listMessageBans()))
  ipcMain.handle(IPC.banCreate, async (_event, ip: string) => api().createMessageBan(ip))
  ipcMain.handle(IPC.banDelete, async (_event, id: number) => api().deleteMessageBan(id))

  ipcMain.handle(IPC.siteUploadBackground, async (): Promise<BackgroundUploadResult> => {
    const window = BrowserWindow.getAllWindows()[0]
    const picked = await dialog.showOpenDialog(window, {
      title: 'Background image',
      properties: ['openFile'],
      filters: [{ name: 'Images', extensions: ['png', 'jpg', 'jpeg', 'webp', 'bmp'] }]
    })
    if (picked.canceled || picked.filePaths.length === 0) {
      return { cancelled: true, bytes: 0, detail: 'cancelled' }
    }
    const raw = await readFile(picked.filePaths[0])
    const jpeg = await toBackgroundJpeg(raw)
    if (!jpeg) {
      return { cancelled: false, bytes: 0, detail: 'decode failed' }
    }
    await api().uploadBackground(jpeg, 'image/jpeg')
    return { cancelled: false, bytes: jpeg.length, detail: 'uploaded' }
  })
}

function toSnapshotView(snapshot: DiagnosticsSnapshot): SnapshotView {
  const media = snapshot.media
  return {
    media: media
      ? {
          state: media.state,
          title: media.title,
          artist: media.artist,
          album: media.album,
          app: media.app,
          cover_url: media.cover_url,
          position_ms: media.position_ms,
          duration_ms: media.duration_ms
        }
      : null,
    coverDataUrl: snapshot.coverBytes
      ? `data:image/jpeg;base64,${snapshot.coverBytes.toString('base64')}`
      : null,
    system: snapshot.system,
    collectedAt: snapshot.collectedAt
  }
}

function total(data: unknown, fallback: number): number {
  if (data && typeof data === 'object') {
    const value = (data as Record<string, unknown>)['total']
    if (typeof value === 'number') {
      return value
    }
  }
  return fallback
}

function diaryPayload(payload: Partial<DiaryItem>): Record<string, unknown> {
  const result: Record<string, unknown> = {}
  if (typeof payload.title === 'string') {
    result['title'] = payload.title
  }
  if (typeof payload.content === 'string') {
    result['content'] = payload.content
  }
  if (payload.mood !== undefined) {
    result['mood'] = payload.mood
  }
  if (Array.isArray(payload.tags)) {
    result['tags'] = payload.tags
  }
  return result
}

function friendPayload(payload: Partial<FriendItem>): Record<string, unknown> {
  const result: Record<string, unknown> = {}
  if (typeof payload.name === 'string') {
    result['name'] = payload.name
  }
  if (typeof payload.url === 'string') {
    result['url'] = payload.url
  }
  if (payload.avatar_url !== undefined) {
    result['avatar_url'] = payload.avatar_url
  }
  if (payload.description !== undefined) {
    result['description'] = payload.description
  }
  if (typeof payload.sort === 'number') {
    result['sort'] = payload.sort
  }
  return result
}

export function sitePayload(config: AppConfig): Record<string, unknown> {
  return { ...config.site }
}
