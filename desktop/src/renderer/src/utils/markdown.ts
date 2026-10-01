const ESCAPE_MAP: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;'
}

function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, (char) => ESCAPE_MAP[char] ?? char)
}

const INLINE_RULES: Array<{ pattern: RegExp; replace: string }> = [
  { pattern: /\*\*(.+?)\*\*/g, replace: '<b>$1</b>' },
  { pattern: /\*(.+?)\*/g, replace: '<i>$1</i>' },
  { pattern: /`([^`]+)`/g, replace: '<code>$1</code>' },
  { pattern: /\[([^\]]+)\]\(([^)]+)\)/g, replace: '<a href="$2" target="_blank" rel="noreferrer">$1</a>' }
]

function inline(text: string): string {
  let result = escapeHtml(text)
  for (const rule of INLINE_RULES) {
    result = result.replace(rule.pattern, rule.replace)
  }
  return result
}

const HEADING_PATTERN = /^(#{1,3}) (.+)$/
const UNORDERED_PATTERN = /^- (.+)$/
const ORDERED_PATTERN = /^\d+\. (.+)$/
const QUOTE_PATTERN = /^> (.+)$/
const RULE_PATTERN = /^-{3,}$/

export function markdownToHtml(text: string): string {
  const lines = text.split(/\r?\n/).map((line) => line.trimEnd())
  const output: string[] = []
  let listTag: 'ul' | 'ol' | null = null

  const closeList = (): void => {
    if (listTag) {
      output.push(`</${listTag}>`)
      listTag = null
    }
  }

  for (const line of lines) {
    const heading = HEADING_PATTERN.exec(line)
    const unordered = UNORDERED_PATTERN.exec(line)
    const ordered = ORDERED_PATTERN.exec(line)
    const quote = QUOTE_PATTERN.exec(line)

    if (unordered || ordered) {
      const tag: 'ul' | 'ol' = unordered ? 'ul' : 'ol'
      if (listTag !== tag) {
        closeList()
        output.push(`<${tag}>`)
        listTag = tag
      }
      output.push(`<li>${inline((unordered ?? ordered)?.[1] ?? '')}</li>`)
      continue
    }

    closeList()

    if (heading) {
      const level = heading[1].length
      output.push(`<h${level}>${inline(heading[2])}</h${level}>`)
      continue
    }
    if (quote) {
      output.push(`<blockquote>${inline(quote[1])}</blockquote>`)
      continue
    }
    if (RULE_PATTERN.test(line)) {
      output.push('<hr/>')
      continue
    }
    if (!line) {
      continue
    }
    output.push(`<p>${inline(line)}</p>`)
  }

  closeList()
  return output.join('\n')
}
