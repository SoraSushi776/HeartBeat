import type {
  ApiEnvelope,
  DiaryList,
  FriendLink,
  GithubData,
  StatusData,
} from "../types/protocol"

/** 请求 JSON 接口并解包 data，失败时抛错 */
async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { Accept: "application/json" },
    ...init,
  })
  const body = (await response.json()) as ApiEnvelope<T>
  if (!response.ok || !body.ok || body.data === undefined) {
    const message = body.error?.message ?? `request failed: ${path}`
    throw new Error(message)
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

/** 拉取友情链接列表 */
export function fetchFriends(): Promise<FriendLink[]> {
  return requestJson<FriendLink[]>("/api/v1/friends")
}

/** 拉取服务端缓存的 GitHub 资料 */
export function fetchGithub(): Promise<GithubData> {
  return requestJson<GithubData>("/api/v1/github")
}
