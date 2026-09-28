/** 将服务端返回的站内资源路径解析为可加载 URL */
export function resolveAssetUrl(path: string | null | undefined): string {
  if (!path) {
    return ""
  }
  if (/^(https?:|data:|blob:)/i.test(path)) {
    return path
  }
  const base = window.location.origin
  if (path.startsWith("/")) {
    return new URL(path, base).toString()
  }
  return new URL(path, window.location.href).toString()
}
