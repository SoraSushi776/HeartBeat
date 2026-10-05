import MarkdownIt from "markdown-it"
import { sanitizeHtml } from "./sanitize"

const RENDERER = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
})

RENDERER.renderer.rules.link_open = (tokens, idx, options, _env, self) => {
  tokens[idx].attrSet("target", "_blank")
  tokens[idx].attrSet("rel", "noopener noreferrer")
  return self.renderToken(tokens, idx, options)
}

interface StripRule {
  pattern: RegExp
  replace: string
}

const STRIP_RULES: StripRule[] = [
  { pattern: /```[^\n]*\n?([\s\S]*?)```/g, replace: "$1" },
  { pattern: /`([^`]+)`/g, replace: "$1" },
  { pattern: /!\[([^\]]*)\]\([^)]*\)/g, replace: "$1" },
  { pattern: /\[([^\]]*)\]\([^)]*\)/g, replace: "$1" },
  { pattern: /\*\*([^*]+)\*\*/g, replace: "$1" },
  { pattern: /__([^_]+)__/g, replace: "$1" },
  { pattern: /\*([^*]+)\*/g, replace: "$1" },
  { pattern: /(^|[^\w])_([^_\n]+)_(?![\w])/g, replace: "$1$2" },
  { pattern: /~~([^~]+)~~/g, replace: "$1" },
  { pattern: /<\/?[a-zA-Z][^>]*>/g, replace: "" },
  { pattern: /^\s{0,3}#{1,6}\s+/gm, replace: "" },
  { pattern: /^\s{0,3}>\s?/gm, replace: "" },
  { pattern: /^\s{0,3}(?:[-*+]|\d+\.)\s+/gm, replace: "" },
  { pattern: /^\s{0,3}\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$/gm, replace: "" },
  { pattern: /\|/g, replace: " " },
  { pattern: /^\s{0,3}(?:[-*_]\s*){3,}$/gm, replace: "" },
  { pattern: /\\([\\`*_{}[\]()#+\-.!|>~])/g, replace: "$1" },
]

/** 将 Markdown 正文渲染为清洗过的 HTML 片段 */
export function renderMarkdown(text: string): string {
  if (!text) {
    return ""
  }
  return sanitizeHtml(RENDERER.render(text))
}

/** 去掉 Markdown 标记，取可用于摘要与搜索的纯文本 */
export function stripMarkdown(text: string): string {
  let result = text
  for (const rule of STRIP_RULES) {
    result = result.replace(rule.pattern, rule.replace)
  }
  return result.trim()
}
