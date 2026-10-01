import type { ReactNode } from 'react'
import { useEffect, useState } from 'react'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogTitle from '@mui/material/DialogTitle'
import Divider from '@mui/material/Divider'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'

import { useTranslate } from '../i18n'
import { colorVar } from '../theme/material-you'
import { formatDateTime } from '../utils/format'
import type { MessageItem } from '@shared/ipc'

export const REPLY_MAX_LENGTH = 500

interface ReplyDialogProps {
  open: boolean
  message: MessageItem | null
  busy?: boolean
  onSend: (content: string) => void
  onClose: () => void
}

export function ReplyDialog({ open, message, busy, onSend, onClose }: ReplyDialogProps): ReactNode {
  const t = useTranslate()
  const [content, setContent] = useState('')

  useEffect(() => {
    if (open) {
      setContent('')
    }
  }, [open, message?.id])

  const trimmed = content.trim()
  const canSend = trimmed.length > 0 && trimmed.length <= REPLY_MAX_LENGTH && !busy

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t('messages.reply_title')}</DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Box
          sx={{
            borderRadius: 3,
            p: 1.5,
            backgroundColor: colorVar('surface-container-highest')
          }}
        >
          <Typography variant="caption" sx={{ color: colorVar('on-surface-variant') }}>
            {t('messages.original')} · {message?.author || t('messages.anonymous')} ·{' '}
            {formatDateTime(message?.created_ts)}
          </Typography>
          <Typography variant="body2" sx={{ mt: 0.5, whiteSpace: 'pre-wrap' }}>
            {message?.content}
          </Typography>
        </Box>

        {message && message.replies.length > 0 ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Typography variant="subtitle1">{t('messages.existing_replies')}</Typography>
            {message.replies.map((reply) => (
              <Box key={reply.id}>
                <Typography variant="caption" sx={{ color: colorVar('on-surface-variant') }}>
                  {formatDateTime(reply.created_ts)}
                </Typography>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {reply.content}
                </Typography>
                <Divider sx={{ mt: 1 }} />
              </Box>
            ))}
          </Box>
        ) : null}

        <TextField
          label={t('messages.reply_placeholder')}
          value={content}
          onChange={(event) => setContent(event.target.value.slice(0, REPLY_MAX_LENGTH))}
          multiline
          minRows={4}
          fullWidth
          helperText={t('messages.char_count', { count: trimmed.length })}
        />
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button variant="text" onClick={onClose}>
          {t('common.cancel')}
        </Button>
        <Button variant="contained" disabled={!canSend} onClick={() => onSend(trimmed)}>
          {t('messages.reply_send')}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
