import MarkdownIt from 'markdown-it'

const RENDERER = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true
})

RENDERER.renderer.rules.link_open = (tokens, idx, options, _env, self) => {
  tokens[idx].attrSet('target', '_blank')
  tokens[idx].attrSet('rel', 'noopener noreferrer')
  return self.renderToken(tokens, idx, options)
}

export function markdownToHtml(text: string): string {
  return text ? RENDERER.render(text) : ''
}
