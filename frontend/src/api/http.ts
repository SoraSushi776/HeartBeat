import type {
  ApiEnvelope,
  Diary,
  DiaryList,
  FriendLink,
  GithubData,
  Message,
  MessageList,
  SiteInfo,
  StatusData,
} from "../types/protocol"

/** 带 HTTP 状态码的接口错误。 */
export class ApiRequestError extends Error {
  /** 创建带状态码的接口错误。 */
  constructor(message: string, readonly status: number) {
    super(message)
  }
}

/** 请求 JSON 接口并解包 data，失败时抛错 */
async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { Accept: "application/json" },
    ...init,
  })
  const body = (await response.json()) as ApiEnvelope<T>
  if (!response.ok || !body.ok || body.data === undefined) {
    const message = body.error?.message ?? `request failed: ${path}`
    throw new ApiRequestError(message, response.status)
  }
  return body.data
}

/** 拉取全量实时状态 */
export function fetchStatus(clientId?: string): Promise<StatusData> {
  const query = clientId ? `?client_id=${encodeURIComponent(clientId)}` : ""
  return requestJson<StatusData>(`/api/v1/status${query}`)
}

/** 拉取日记分页列表 */
export function fetchDiaries(limit = 50, offset = 0): Promise<DiaryList> {
  return requestJson<DiaryList>(`/api/v1/diaries?limit=${limit}&offset=${offset}`)
}

/** 按 id 拉取单篇日记。 */
export function fetchDiary(id: number): Promise<Diary> {
  return requestJson<Diary>(`/api/v1/diaries/${id}`)
}

/** 拉取友情链接列表 */
export function fetchFriends(): Promise<FriendLink[]> {
  return requestJson<FriendLink[]>("/api/v1/friends")
}

/** 拉取服务端缓存的 GitHub 资料 */
export function fetchGithub(): Promise<GithubData> {
  return requestJson<GithubData>("/api/v1/github")
}

/** 拉取留言分页列表 */
export function fetchMessages(limit = 50, offset = 0): Promise<MessageList> {
  return requestJson<MessageList>(`/api/v1/messages?limit=${limit}&offset=${offset}`)
}

/** 发布一条留言 */
export function createMessage(payload: {
  author?: string
  content: string
  expose_ip?: boolean
}): Promise<Message> {
  return requestJson<Message>("/api/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
}

/** 拉取站点背景图 URL */
export function fetchBackground(): Promise<{ url?: string | null }> {
  return requestJson<{ url?: string | null }>("/api/v1/background")
}

/** 拉取站点标题与描述文案 */
export function fetchSite(): Promise<SiteInfo> {
  return requestJson<SiteInfo>("/api/v1/site")
}
