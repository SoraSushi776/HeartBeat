const DROP_TAGS = new Set(["SCRIPT", "STYLE", "IFRAME", "OBJECT", "EMBED", "LINK", "META"])

/** 清洗服务端 HTML，去掉脚本与事件属性后返回正文片段 */
export function sanitizeHtml(html: string): string {
  const doc = new DOMParser().parseFromString(html, "text/html")
  const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_ELEMENT)
  const doomed: Element[] = []
  while (walker.nextNode()) {
    const el = walker.currentNode as Element
    if (DROP_TAGS.has(el.tagName)) {
      doomed.push(el)
      continue
    }
    for (const attr of Array.from(el.attributes)) {
      const name = attr.name.toLowerCase()
      const isScriptHref = name === "href" && attr.value.trim().toLowerCase().startsWith("javascript:")
      if (name.startsWith("on") || isScriptHref) {
        el.removeAttribute(attr.name)
      }
    }
  }
  for (const el of doomed) {
    el.remove()
  }
  return doc.body.innerHTML
}
