import type { ReactNode } from 'react'
import { useEffect, useMemo, useState } from 'react'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Divider from '@mui/material/Divider'
import IconButton from '@mui/material/IconButton'
import List from '@mui/material/List'
import ListItemButton from '@mui/material/ListItemButton'
import Tab from '@mui/material/Tab'
import Tabs from '@mui/material/Tabs'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import AddIcon from '@mui/icons-material/Add'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline'

import { ConfirmDialog } from '../components/ConfirmDialog'
import { PageScaffold } from '../components/PageScaffold'
import { useHeaderActions } from '../shell/header'
import { StateBlock } from '../components/StateBlock'
import { useLanguage, useTranslate } from '../i18n'
import { colorVar } from '../theme/material-you'
import { bridge, errorMessage } from '../utils/bridge'
import { formatDate, formatRelative } from '../utils/format'
import { useAsync } from '../utils/hooks'
import { markdownToHtml } from '../utils/markdown'
import type { DiaryItem } from '@shared/ipc'

interface Draft {
  id: number | null
  title: string
  mood: string
  tags: string
  content: string
}

const EMPTY_DRAFT: Draft = { id: null, title: '', mood: '', tags: '', content: '' }

function toDraft(item: DiaryItem): Draft {
  return {
    id: item.id,
    title: item.title,
    mood: item.mood ?? '',
    tags: item.tags.join(', '),
    content: item.content
  }
}

function splitTags(raw: string): string[] {
  return raw
    .split(',')
    .map((item) => item.trim())
    .filter((item) => item.length > 0)
}

export function DiaryPage(): ReactNode {
  const t = useTranslate()
  const language = useLanguage((state) => state.language)
  const list = useAsync(() => bridge.diary.list(), [])
  const [draft, setDraft] = useState<Draft>(EMPTY_DRAFT)
  const [tab, setTab] = useState(0)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [confirming, setConfirming] = useState(false)

  const items = useMemo(() => list.data?.items ?? [], [list.data])

  useEffect(() => {
    if (items.length > 0 && draft.id === null && !draft.title && !draft.content) {
      setDraft(toDraft(items[0]))
    }
  }, [items, draft.id, draft.title, draft.content])

  const previewHtml = useMemo(() => markdownToHtml(draft.content), [draft.content])

  const save = async (): Promise<void> => {
    setBusy(true)
    setError(null)
    try {
      const payload = {
        title: draft.title.trim() || t('diary.untitled'),
        content: draft.content,
        mood: draft.mood.trim() || null,
        tags: splitTags(draft.tags)
      }
      if (draft.id === null) {
        const created = await bridge.diary.create(payload)
        setDraft(toDraft(created))
      } else {
        const updated = await bridge.diary.update(draft.id, payload)
        setDraft(toDraft(updated))
      }
      list.reload()
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setBusy(false)
    }
  }

  const remove = async (): Promise<void> => {
    if (draft.id === null) {
      return
    }
    setBusy(true)
    setError(null)
    try {
      await bridge.diary.remove(draft.id)
      setDraft(EMPTY_DRAFT)
      setConfirming(false)
      list.reload()
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setBusy(false)
    }
  }

  const headerActions = useMemo(
    () => (
      <Box sx={{ display: 'flex', gap: 1 }}>
        <Button
          variant="tonal"
          startIcon={<AddIcon />}
          onClick={() => {
            setDraft(EMPTY_DRAFT)
            setTab(0)
          }}
        >
          {t('diary.new')}
        </Button>
        <Button variant="contained" onClick={() => void save()} disabled={busy}>
          {t('common.save')}
        </Button>
      </Box>
    ),
    [busy, t]
  )
  useHeaderActions(headerActions)

  return (
    <PageScaffold fill>
      <Box sx={{ display: 'flex', gap: 2, flexGrow: 1, minHeight: 0 }}>
        <Box
          sx={{
            width: 300,
            flexShrink: 0,
            borderRadius: 'var(--md-sys-shape-corner-large)',
            backgroundColor: colorVar('surface-container-low'),
            border: `1px solid ${colorVar('outline-variant')}`,
            overflowY: 'auto',
            p: 1
          }}
        >
          <StateBlock
            loading={list.loading}
            error={list.error}
            empty={items.length === 0}
            emptyText={t('diary.empty')}
            onRetry={list.reload}
          >
            <List dense disablePadding>
              {items.map((item) => (
                <ListItemButton
                  key={item.id}
                  selected={draft.id === item.id}
                  onClick={() => {
                    setDraft(toDraft(item))
                    setTab(0)
                  }}
                  sx={{ flexDirection: 'column', alignItems: 'flex-start', py: 1, mb: 0.5 }}
                >
                  <Typography variant="body2" sx={{ fontWeight: 500 }} noWrap>
                    {item.title || t('diary.untitled')}
                  </Typography>
                  <Typography variant="caption" sx={{ color: colorVar('on-surface-variant') }}>
                    {formatDate(item.created_ts)} · {item.tags.join(' / ') || t('common.none')}
                  </Typography>
                </ListItemButton>
              ))}
            </List>
          </StateBlock>
        </Box>

        <Box
          sx={{
            flexGrow: 1,
            minWidth: 0,
            display: 'flex',
            flexDirection: 'column',
            borderRadius: 'var(--md-sys-shape-corner-large)',
            backgroundColor: colorVar('surface-container-low'),
            border: `1px solid ${colorVar('outline-variant')}`,
            overflow: 'hidden'
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 2, pt: 1 }}>
            <Tabs value={tab} onChange={(_event, value: number) => setTab(value)} sx={{ flexGrow: 1 }}>
              <Tab label={t('diary.content')} />
              <Tab label={t('diary.preview')} />
            </Tabs>
            {draft.id !== null ? (
              <IconButton
                aria-label={t('common.delete')}
                onClick={() => setConfirming(true)}
                disabled={busy}
                sx={{ color: colorVar('error') }}
              >
                <DeleteOutlineIcon fontSize="small" />
              </IconButton>
            ) : null}
          </Box>
          <Divider />

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, p: 2, overflowY: 'auto' }}>
            <TextField
              label={t('diary.title')}
              value={draft.title}
              onChange={(event) => setDraft({ ...draft, title: event.target.value })}
              fullWidth
            />
            <Box sx={{ display: 'flex', gap: 1.5 }}>
              <TextField
                label={t('diary.mood')}
                value={draft.mood}
                onChange={(event) => setDraft({ ...draft, mood: event.target.value })}
                sx={{ flex: 1 }}
              />
              <TextField
                label={t('diary.tags')}
                value={draft.tags}
                onChange={(event) => setDraft({ ...draft, tags: event.target.value })}
                sx={{ flex: 2 }}
              />
            </Box>

            {tab === 0 ? (
              <>
                <TextField
                  label={t('diary.content')}
                  value={draft.content}
                  onChange={(event) => setDraft({ ...draft, content: event.target.value })}
                  multiline
                  minRows={16}
                  fullWidth
                />
                <Typography variant="caption" sx={{ color: colorVar('on-surface-variant') }}>
                  {t('diary.markdown_hint')}
                </Typography>
              </>
            ) : (
              <Box
                sx={{
                  minHeight: 360,
                  px: 1,
                  '& h1, & h2, & h3': { margin: '12px 0 6px' },
                  '& p': { margin: '6px 0', lineHeight: 1.7 },
                  '& ul, & ol': { margin: '6px 0', paddingInlineStart: '24px' },
                  '& blockquote': {
                    margin: '8px 0',
                    paddingInlineStart: '12px',
                    borderInlineStart: `3px solid ${colorVar('outline-variant')}`,
                    color: colorVar('on-surface-variant')
                  },
                  '& code': {
                    backgroundColor: colorVar('surface-container-highest'),
                    borderRadius: '4px',
                    padding: '1px 4px'
                  },
                  '& a': { color: colorVar('primary') },
                  '& hr': { border: 'none', borderTop: `1px solid ${colorVar('outline-variant')}` }
                }}
                dangerouslySetInnerHTML={{ __html: previewHtml }}
              />
            )}

            {draft.id !== null ? (
              <Typography variant="caption" sx={{ color: colorVar('on-surface-variant') }}>
                {items.find((item) => item.id === draft.id)
                  ? `${t('diary.created')} ${formatRelative(
                      items.find((item) => item.id === draft.id)?.created_ts ?? null,
                      language
                    )}`
                  : ''}
              </Typography>
            ) : null}
            {error ? (
              <Typography variant="body2" sx={{ color: colorVar('error') }}>
                {error}
              </Typography>
            ) : null}
          </Box>
        </Box>
      </Box>

      <ConfirmDialog
        open={confirming}
        title={t('diary.delete_confirm')}
        destructive
        confirmLabel={t('common.delete')}
        onConfirm={() => void remove()}
        onCancel={() => setConfirming(false)}
      />
    </PageScaffold>
  )
}
