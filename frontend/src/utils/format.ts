/** 取毫秒时间戳的本地时间文案 */
export function formatTs(ts: number | null | undefined): string {
  if (!ts) {
    return "—"
  }
  return new Date(ts).toLocaleString()
}

/** 取毫秒时长的分秒文案 */
export function formatDuration(ms: number | null | undefined): string {
  if (ms === null || ms === undefined || !Number.isFinite(ms) || ms < 0) {
    return "--:--"
  }
  const total = Math.floor(ms / 1000)
  const minutes = Math.floor(total / 60)
  const seconds = total % 60
  return `${minutes}:${String(seconds).padStart(2, "0")}`
}

/** 取时间戳相对 nowMs 的中文相对时间 */
export function formatRelative(ts: number | null | undefined, nowMs: number): string {
  if (!ts) {
    return "—"
  }
  const diff = Math.max(0, nowMs - ts)
  if (diff < 60_000) {
    return "刚刚"
  }
  if (diff < 3_600_000) {
    return `${Math.floor(diff / 60_000)} 分钟前`
  }
  if (diff < 86_400_000) {
    return `${Math.floor(diff / 3_600_000)} 小时前`
  }
  return `${Math.floor(diff / 86_400_000)} 天前`
}

/** 取时间戳的年月分组标题 */
export function monthLabel(ts: number): string {
  const date = new Date(ts)
  return `${date.getFullYear()} 年 ${date.getMonth() + 1} 月`
}
