import type { ReactNode } from 'react'
import { useMemo } from 'react'
import Box from '@mui/material/Box'
import type { SxProps, Theme } from '@mui/material/styles'

import { colorVar } from '../theme/material-you'
import { markdownToHtml } from '../utils/markdown'

interface MarkdownPreviewProps {
  content: string
}

const PREVIEW_SX: SxProps<Theme> = {
  minHeight: 360,
  px: 1,
  lineHeight: 1.75,
  overflowWrap: 'anywhere',
  '& > :first-of-type': { marginTop: 0 },
  '& > :last-child': { marginBottom: 0 },
  '& h1, & h2, & h3, & h4, & h5, & h6': { margin: '18px 0 8px', fontWeight: 600, lineHeight: 1.35 },
  '& h1': { fontSize: '1.35rem' },
  '& h2': { fontSize: '1.2rem' },
  '& h3': { fontSize: '1.08rem' },
  '& h4, & h5, & h6': { fontSize: '1rem', color: colorVar('on-surface-variant') },
  '& p': { margin: '10px 0' },
  '& ul, & ol': { margin: '10px 0', paddingInlineStart: '24px' },
  '& li': { margin: '4px 0' },
  '& blockquote': {
    margin: '12px 0',
    paddingInlineStart: '12px',
    borderInlineStart: `3px solid ${colorVar('outline-variant')}`,
    color: colorVar('on-surface-variant')
  },
  '& code': {
    backgroundColor: colorVar('surface-container-highest'),
    borderRadius: '4px',
    padding: '1px 4px',
    fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
    fontSize: '0.88em'
  },
  '& pre': {
    margin: '12px 0',
    padding: '12px 14px',
    overflowX: 'auto',
    borderRadius: '12px',
    backgroundColor: colorVar('surface-container-highest'),
    '& code': { backgroundColor: 'transparent', padding: 0, fontSize: '0.85rem' }
  },
  '& img': { maxWidth: '100%', borderRadius: '12px', margin: '10px 0' },
  '& hr': { border: 'none', borderTop: `1px solid ${colorVar('outline-variant')}`, margin: '18px 0' },
  '& table': { width: '100%', margin: '14px 0', borderCollapse: 'collapse', fontSize: '0.92rem' },
  '& th, & td': {
    padding: '7px 10px',
    border: `1px solid ${colorVar('outline-variant')}`,
    textAlign: 'start'
  },
  '& th': { backgroundColor: colorVar('surface-container-highest') },
  '& a': { color: colorVar('primary') }
}

export function MarkdownPreview({ content }: MarkdownPreviewProps): ReactNode {
  const html = useMemo(() => markdownToHtml(content), [content])

  return <Box sx={PREVIEW_SX} dangerouslySetInnerHTML={{ __html: html }} />
}
