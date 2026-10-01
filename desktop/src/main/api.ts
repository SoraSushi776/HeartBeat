import { logger } from './logger'
import {
  API_PREFIX,
  HEADER_API_KEY,
  HEADER_CLIENT_VERSION,
  HEADER_HEARTBEAT_TS,
  type HeartbeatPayload
} from './protocol'

export class ApiError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

export interface ApiSettings {
  baseUrl: string
  apiKey: string
  timeoutSeconds: number
  clientVersion: string
  clientId: string
}

export interface HeartbeatResponse {
  screenshot_upload_url?: string
  [key: string]: unknown
}

type Body = Record<string, unknown> | undefined

export class HeartbeatApi {
  private settings: ApiSettings

  constructor(settings: ApiSettings) {
    this.settings = settings
  }

  update(settings: ApiSettings): void {
    this.settings = settings
  }

  get baseUrl(): string {
    return this.settings.baseUrl.replace(/\/+$/, '')
  }

  async heartbeat(payload: HeartbeatPayload): Promise<HeartbeatResponse> {
    const data = await this.request('POST', '/heartbeat', payload as unknown as Record<string, unknown>)
    if (data && typeof data === 'object') {
      return data as HeartbeatResponse
    }
    return {}
  }

  async putCover(bytes: Buffer): Promise<string | null> {
    const response = await this.raw('PUT', `${API_PREFIX}/cover/${this.settings.clientId}`, {
      body: new Uint8Array(bytes),
      contentType: 'image/jpeg'
    })
    const url = (response as { url?: unknown })?.url
    return typeof url === 'string' ? url : null
  }

  async putScreenshot(uploadUrl: string, webp: Buffer, ts: number | null): Promise<void> {
    const url = uploadUrl.startsWith('/') ? `${this.baseUrl}${uploadUrl}` : uploadUrl
    const headers: Record<string, string> = { 'Content-Type': 'image/webp' }
    if (typeof ts === 'number') {
      headers[HEADER_HEARTBEAT_TS] = String(ts)
    }
    const response = await this.fetchRaw(url, 'PUT', new Uint8Array(webp), headers)
    if (!response.ok) {
      throw new ApiError(`HTTP ${response.status}`)
    }
  }

  listDiaries(): Promise<unknown> {
    return this.request('GET', '/diaries')
  }

  createDiary(payload: Body): Promise<unknown> {
    return this.request('POST', '/diaries', payload)
  }

  updateDiary(id: number, payload: Body): Promise<unknown> {
    return this.request('PATCH', `/diaries/${id}`, payload)
  }

  deleteDiary(id: number): Promise<unknown> {
    return this.request('DELETE', `/diaries/${id}`)
  }

  listFriends(): Promise<unknown> {
    return this.request('GET', '/friends')
  }

  createFriend(payload: Body): Promise<unknown> {
    return this.request('POST', '/friends', payload)
  }

  updateFriend(id: number, payload: Body): Promise<unknown> {
    return this.request('PATCH', `/friends/${id}`, payload)
  }

  deleteFriend(id: number): Promise<unknown> {
    return this.request('DELETE', `/friends/${id}`)
  }

  async setGithubToken(token: string, login: string): Promise<unknown> {
    const payload: Record<string, unknown> = { token }
    if (login) {
      payload['login'] = login
    }
    return this.request('POST', '/github/token', payload)
  }

  updateSite(payload: Record<string, unknown>): Promise<unknown> {
    return this.request('PUT', '/site', payload)
  }

  listMessages(limit = 50, offset = 0): Promise<unknown> {
    return this.request('GET', `/messages/admin?limit=${limit}&offset=${offset}`)
  }

  deleteMessage(id: number): Promise<unknown> {
    return this.request('DELETE', `/messages/${id}`)
  }

  createMessageReply(id: number, content: string): Promise<unknown> {
    return this.request('POST', `/messages/${id}/replies`, { content })
  }

  listMessageBans(): Promise<unknown> {
    return this.request('GET', '/messages/bans')
  }

  createMessageBan(ip: string): Promise<unknown> {
    return this.request('POST', '/messages/bans', { ip })
  }

  deleteMessageBan(id: number): Promise<unknown> {
    return this.request('DELETE', `/messages/bans/${id}`)
  }

  async uploadBackground(data: Buffer, contentType: string): Promise<unknown> {
    return this.raw('PUT', `${API_PREFIX}/background`, {
      body: new Uint8Array(data),
      contentType,
      timeoutSeconds: Math.max(this.settings.timeoutSeconds, 30)
    })
  }

  private async request(method: string, path: string, body?: Body): Promise<unknown> {
    const url = `${this.baseUrl}${API_PREFIX}${path}`
    const headers: Record<string, string> = { [HEADER_API_KEY]: this.settings.apiKey }
    if (body !== undefined) {
      headers['Content-Type'] = 'application/json'
    }
    const response = await this.fetchRaw(
      url,
      method,
      body === undefined ? undefined : JSON.stringify(body),
      headers
    )
    return this.parseEnvelope(response, method, path)
  }

  private async raw(
    method: string,
    path: string,
    options: { body: Uint8Array; contentType: string; timeoutSeconds?: number }
  ): Promise<unknown> {
    const url = path.startsWith('http') ? path : `${this.baseUrl}${path}`
    const response = await this.fetchRaw(
      url,
      method,
      options.body,
      { 'Content-Type': options.contentType },
      options.timeoutSeconds
    )
    return this.parseEnvelope(response, method, path)
  }

  private async fetchRaw(
    url: string,
    method: string,
    body?: Uint8Array | string,
    extraHeaders: Record<string, string> = {},
    timeoutSeconds?: number
  ): Promise<Response> {
    const timeout = timeoutSeconds ?? this.settings.timeoutSeconds
    const headers: Record<string, string> = {
      [HEADER_API_KEY]: this.settings.apiKey,
      [HEADER_CLIENT_VERSION]: this.settings.clientVersion,
      ...extraHeaders
    }
    try {
      return await fetch(url, {
        method,
        headers,
        body,
        signal: AbortSignal.timeout(Math.max(timeout * 1000, 1000))
      })
    } catch (error) {
      logger.debug(`Request failed: ${method} ${url} ${String(error)}`)
      throw new ApiError(String(error))
    }
  }

  private async parseEnvelope(response: Response, method: string, path: string): Promise<unknown> {
    let body: unknown
    try {
      body = await response.json()
    } catch {
      throw new ApiError(`HTTP ${response.status}`)
    }
    if (typeof body !== 'object' || body === null) {
      throw new ApiError(`HTTP ${response.status}`)
    }
    const envelope = body as { ok?: unknown; data?: unknown; error?: { message?: unknown } }
    if (envelope.ok) {
      return envelope.data
    }
    const message =
      typeof envelope.error?.message === 'string'
        ? envelope.error.message
        : `HTTP ${response.status}`
    logger.debug(`API rejected: ${method} ${path} ${message}`)
    throw new ApiError(message)
  }
}
