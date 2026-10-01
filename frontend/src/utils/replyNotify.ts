import type { Message } from "../types/protocol"

const STORAGE_KEY = "heartbeat-message-replies"

export interface ReplyNotice {
  message: Message
}

/** 读取已通知过回复的留言 ID，首次访问返回 null 表示尚未建立基线 */
function readSeen(): number[] | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (raw === null) {
      return null
    }
    const parsed = JSON.parse(raw) as unknown
    if (!Array.isArray(parsed)) {
      return null
    }
    return parsed.filter((item): item is number => typeof item === "number")
  } catch {
    return null
  }
}

/** 写入已通知过回复的留言 ID */
function writeSeen(ids: number[]): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(ids))
  } catch {
    return
  }
}

/** 检出首次出现回复的留言，首次访问只写入基线不产生通知 */
export function detectReplyNotices(messages: Message[]): ReplyNotice[] {
  const replied = messages.filter((message) => (message.replies?.length ?? 0) > 0)
  const seen = readSeen()
  if (seen === null) {
    writeSeen(replied.map((message) => message.id))
    return []
  }
  const known = new Set(seen)
  const fresh = replied.filter((message) => !known.has(message.id))
  const alive = new Set(messages.map((message) => message.id))
  const merged = [...new Set([...seen, ...replied.map((message) => message.id)])].filter((id) =>
    alive.has(id),
  )
  writeSeen(merged)
  return fresh.map((message) => ({ message }))
}

/** 滚动定位到某条留言并短暂高亮 */
export function focusMessage(messageId: number): void {
  const target = document.getElementById(`message-${messageId}`)
  if (!target) {
    return
  }
  target.scrollIntoView({ behavior: "smooth", block: "center" })
  target.classList.add("is-highlighted")
  window.setTimeout(() => target.classList.remove("is-highlighted"), 2400)
}
