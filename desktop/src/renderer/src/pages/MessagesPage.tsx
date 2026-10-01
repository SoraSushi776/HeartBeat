import type { ReactNode } from 'react'
import { useMemo, useState } from 'react'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import Divider from '@mui/material/Divider'
import IconButton from '@mui/material/IconButton'
import List from '@mui/material/List'
import ListItemButton from '@mui/material/ListItemButton'
import TextField from '@mui/material/TextField'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import BlockIcon from '@mui/icons-material/Block'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline'
import ReplyOutlinedIcon from '@mui/icons-material/ReplyOutlined'
import ShieldOutlinedIcon from '@mui/icons-material/ShieldOutlined'

import { ConfirmDialog } from '../components/ConfirmDialog'
import { PageScaffold } from '../components/PageScaffold'
import { ReplyDialog } from '../components/ReplyDialog'
import { SectionCard } from '../components/SectionCard'
import { StateBlock } from '../components/StateBlock'
import { useLanguage, useTranslate } from '../i18n'
import { colorVar } from '../theme/material-you'
import { bridge, errorMessage } from '../utils/bridge'
import { formatRelative } from '../utils/format'
import { useAsync, useInterval } from '../utils/hooks'
import type { MessageItem } from '@shared/ipc'

const POLL_MS = 8000

export function MessagesPage(): ReactNode {
  const t = useTranslate()
  const language = useLanguage((state) => state.language)
  const messages = useAsync(() => bridge.message.list(), [])
  const bans = useAsync(() => bridge.ban.list(), [])
  const [active, setActive] = useState<MessageItem | null>(null)
  const [replying, setReplying] = useState(false)
  const [deleting, setDeleting] = useState<MessageItem | null>(null)
  const [banning, setBanning] = useState<string | null>(null)
  const [banDraft, setBanDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const items = useMemo(() => messages.data?.items ?? [], [messages.data])
  const current = active ? items.find((item) => item.id === active.id) ?? active : items[0] ?? null

  useInterval(() => {
    messages.reload()
    bans.reload()
  }, POLL_MS)

  const sendReply = async (content: string): Promise<void> => {
    if (!current) {
      return
    }
    setBusy(true)
    try {
      await bridge.message.reply(current.id, content)
      setReplying(false)
      messages.reload()
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setBusy(false)
    }
  }

  const removeMessage = async (): Promise<void> => {
    if (!deleting) {
      return
    }
    setBusy(true)
    try {
      await bridge.message.remove(deleting.id)
      setDeleting(null)
      setActive(null)
      messages.reload()
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setBusy(false)
    }
  }

  const createBan = async (): Promise<void> => {
    const ip = (banning ?? banDraft).trim()
    if (!ip) {
      return
    }
    setBusy(true)
    try {
      await bridge.ban.create(ip)
      setBanning(null)
      setBanDraft('')
      bans.reload()
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setBusy(false)
    }
  }

  const removeBan = async (id: number): Promise<void> => {
    setBusy(true)
    try {
      await bridge.ban.remove(id)
      bans.reload()
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setBusy(false)
    }
  }

  return (
    <PageScaffold
      page="messages"
      title={t('nav.messages')}
      actions={
        <Typography variant="caption" sx={{ color: colorVar('on-surface-variant') }}>
          {t('messages.polling')}
        </Typography>
      }
    >
      {error ? (
        <Typography variant="body2" sx={{ color: colorVar('error') }}>
          {error}
        </Typography>
      ) : null}

      <SectionCard
        title={t('messages.list')}
        action={
          <Button variant="text" size="small" onClick={messages.reload}>
            {t('common.refresh')}
          </Button>
        }
      >
        <StateBlock
          loading={messages.loading}
          error={messages.error}
          empty={items.length === 0}
          emptyText={t('messages.empty')}
          onRetry={messages.reload}
        >
          <List disablePadding sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {items.map((item) => (
              <Box
                key={item.id}
                sx={{
                  borderRadius: 3,
                  border: `1px solid ${colorVar('outline-variant')}`,
                  backgroundColor: current?.id === item.id ? colorVar('surface-container') : 'transparent',
                  p: 1.5,
                  display: 'flex',
                  gap: 1.5
                }}
              >
                <ListItemButton
                  onClick={() => setActive(item)}
                  sx={{ flexGrow: 1, alignItems: 'flex-start', borderRadius: 3, p: 0.5, minWidth: 0 }}
                >
                  <Box sx={{ minWidth: 0, width: '100%' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                      <Typography variant="subtitle1">{item.author || t('messages.anonymous')}</Typography>
                      <Typography variant="caption" sx={{ color: colorVar('on-surface-variant') }}>
                        {item.ip} · {(item.location || t('messages.location_unknown')).trim()}
                      </Typography>
                      <Typography variant="caption" sx={{ color: colorVar('on-surface-variant') }}>
                        {formatRelative(item.created_ts, language)}
                      </Typography>
                    </Box>
                    <Typography variant="body2" sx={{ mt: 0.5, whiteSpace: 'pre-wrap' }}>
                      {item.content}
                    </Typography>
                    {item.replies.length > 0 ? (
                      <Tooltip
                        placement="bottom-start"
                        title={
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                            {item.replies.map((reply) => (
                              <Typography key={reply.id} variant="caption">
                                {reply.content}
                              </Typography>
                            ))}
                          </Box>
                        }
                      >
                        <Chip
                          size="small"
                          sx={{ mt: 1 }}
                          label={t('messages.reply_count', { count: item.replies.length })}
                        />
                      </Tooltip>
                    ) : (
                      <Typography variant="caption" sx={{ color: colorVar('on-surface-variant') }}>
                        {t('messages.no_reply')}
                      </Typography>
                    )}
                  </Box>
                </ListItemButton>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, flexShrink: 0 }}>
                  <Tooltip title={t('messages.reply')}>
                    <IconButton
                      size="small"
                      onClick={() => {
                        setActive(item)
                        setReplying(true)
                      }}
                      sx={{ color: colorVar('primary') }}
                    >
                      <ReplyOutlinedIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title={t('messages.ban')}>
                    <IconButton size="small" onClick={() => setBanning(item.ip)}>
                      <ShieldOutlinedIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title={t('common.delete')}>
                    <IconButton
                      size="small"
                      onClick={() => setDeleting(item)}
                      sx={{ color: colorVar('error') }}
                    >
                      <DeleteOutlineIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              </Box>
            ))}
          </List>
        </StateBlock>
      </SectionCard>

      <SectionCard
        title={t('messages.bans')}
        action={
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <TextField
              size="small"
              placeholder="IP"
              value={banDraft}
              onChange={(event) => setBanDraft(event.target.value)}
              sx={{ width: 180 }}
            />
            <Button variant="tonal" onClick={() => void createBan()} disabled={busy || !banDraft.trim()}>
              {t('messages.ban')}
            </Button>
          </Box>
        }
      >
        <StateBlock
          loading={bans.loading}
          error={bans.error}
          empty={(bans.data?.length ?? 0) === 0}
          emptyText={t('messages.bans_empty')}
          onRetry={bans.reload}
        >
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {(bans.data ?? []).map((ban) => (
              <Chip
                key={ban.id}
                icon={<BlockIcon fontSize="small" />}
                label={ban.ip}
                onDelete={() => void removeBan(ban.id)}
                deleteIcon={<DeleteOutlineIcon fontSize="small" />}
              />
            ))}
          </Box>
        </StateBlock>
        <Divider sx={{ mt: 1 }} />
      </SectionCard>

      <ReplyDialog
        open={replying}
        message={current}
        busy={busy}
        onSend={(content) => void sendReply(content)}
        onClose={() => setReplying(false)}
      />

      <ConfirmDialog
        open={Boolean(deleting)}
        title={t('messages.delete_confirm')}
        destructive
        confirmLabel={t('common.delete')}
        onConfirm={() => void removeMessage()}
        onCancel={() => setDeleting(null)}
      />

      <ConfirmDialog
        open={Boolean(banning)}
        title={t('messages.ban_confirm', { ip: banning ?? '' })}
        destructive
        confirmLabel={t('messages.ban')}
        onConfirm={() => void createBan()}
        onCancel={() => setBanning(null)}
      />
    </PageScaffold>
  )
}
