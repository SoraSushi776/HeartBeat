const MINUTE = 60_000
const HOUR = 60 * MINUTE
const DAY = 24 * HOUR

function pad(value: number): string {
  return value < 10 ? `0${value}` : String(value)
}

export function formatDateTime(ms: number | null | undefined): string {
  if (!ms) {
    return '-'
  }
  const date = new Date(ms)
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export function formatDate(ms: number | null | undefined): string {
  if (!ms) {
    return '-'
  }
  const date = new Date(ms)
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

export function formatRelative(
  ms: number | null | undefined,
  language: 'zh-CN' | 'en-US' = 'zh-CN'
): string {
  if (!ms) {
    return '-'
  }
  const delta = Date.now() - ms
  const zh = language === 'zh-CN'
  if (delta < MINUTE) {
    return zh ? '刚刚' : 'just now'
  }
  if (delta < HOUR) {
    const value = Math.floor(delta / MINUTE)
    return zh ? `${value} 分钟前` : `${value}m ago`
  }
  if (delta < DAY) {
    const value = Math.floor(delta / HOUR)
    return zh ? `${value} 小时前` : `${value}h ago`
  }
  const value = Math.floor(delta / DAY)
  if (value < 30) {
    return zh ? `${value} 天前` : `${value}d ago`
  }
  return formatDate(ms)
}

export function formatDuration(ms: number | null | undefined): string {
  if (!ms || ms <= 0) {
    return '0:00'
  }
  const total = Math.floor(ms / 1000)
  const minutes = Math.floor(total / 60)
  const seconds = total % 60
  return `${minutes}:${pad(seconds)}`
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`
  }
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}
