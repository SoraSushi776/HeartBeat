import { contextBridge, ipcRenderer } from 'electron'

import {
  IPC,
  type AppInfo,
  type BackgroundUploadResult,
  type BanItem,
  type ConfigBundle,
  type DiaryItem,
  type DiaryList,
  type FriendItem,
  type HeartbeatBridge,
  type MessageList,
  type PushRecordView,
  type SaveResult,
  type SetupReport,
  type SnapshotView,
  type Unsubscribe
} from '../shared/ipc'

function subscribe<T>(channel: string, listener: (payload: T) => void): Unsubscribe {
  const handler = (_event: unknown, payload: T): void => listener(payload)
  ipcRenderer.on(channel, handler)
  return () => {
    ipcRenderer.removeListener(channel, handler)
  }
}

const heartbeat: HeartbeatBridge = {
  app: {
    info: (): Promise<AppInfo> => ipcRenderer.invoke(IPC.appInfo),
    platform: process.platform,
    hide: (): Promise<void> => ipcRenderer.invoke(IPC.windowHide),
    show: (): Promise<void> => ipcRenderer.invoke(IPC.windowShow)
  },
  config: {
    load: (): Promise<ConfigBundle> => ipcRenderer.invoke(IPC.configLoad),
    save: (bundle: ConfigBundle): Promise<SaveResult> => ipcRenderer.invoke(IPC.configSave, bundle)
  },
  diagnostics: {
    snapshot: (): Promise<SnapshotView> => ipcRenderer.invoke(IPC.diagnosticsSnapshot),
    history: (): Promise<PushRecordView[]> => ipcRenderer.invoke(IPC.diagnosticsHistory),
    onPushResult: (listener: (record: PushRecordView) => void): Unsubscribe =>
      subscribe(IPC.eventPushResult, listener)
  },
  setup: {
    report: (): Promise<SetupReport> => ipcRenderer.invoke(IPC.setupReport),
    run: (actionId: string): Promise<SetupReport> => ipcRenderer.invoke(IPC.setupAction, actionId)
  },
  diary: {
    list: (): Promise<DiaryList> => ipcRenderer.invoke(IPC.diaryList),
    create: (payload: Partial<DiaryItem>): Promise<DiaryItem> => ipcRenderer.invoke(IPC.diaryCreate, payload),
    update: (id: number, payload: Partial<DiaryItem>): Promise<DiaryItem> => ipcRenderer.invoke(IPC.diaryUpdate, id, payload),
    remove: (id: number): Promise<unknown> => ipcRenderer.invoke(IPC.diaryDelete, id)
  },
  friend: {
    list: (): Promise<FriendItem[]> => ipcRenderer.invoke(IPC.friendList),
    create: (payload: Partial<FriendItem>): Promise<FriendItem> => ipcRenderer.invoke(IPC.friendCreate, payload),
    update: (id: number, payload: Partial<FriendItem>): Promise<FriendItem> => ipcRenderer.invoke(IPC.friendUpdate, id, payload),
    remove: (id: number): Promise<unknown> => ipcRenderer.invoke(IPC.friendDelete, id)
  },
  message: {
    list: (): Promise<MessageList> => ipcRenderer.invoke(IPC.messageList),
    remove: (id: number): Promise<unknown> => ipcRenderer.invoke(IPC.messageDelete, id),
    reply: (id: number, content: string): Promise<unknown> => ipcRenderer.invoke(IPC.messageReply, id, content)
  },
  ban: {
    list: (): Promise<BanItem[]> => ipcRenderer.invoke(IPC.banList),
    create: (ip: string): Promise<unknown> => ipcRenderer.invoke(IPC.banCreate, ip),
    remove: (id: number): Promise<unknown> => ipcRenderer.invoke(IPC.banDelete, id)
  },
  site: {
    uploadBackground: (): Promise<BackgroundUploadResult> => ipcRenderer.invoke(IPC.siteUploadBackground)
  }
}

export type { HeartbeatBridge }

contextBridge.exposeInMainWorld('heartbeat', heartbeat)
