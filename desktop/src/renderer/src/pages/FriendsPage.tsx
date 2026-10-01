import type { ReactNode } from 'react'
import { useEffect, useMemo, useState } from 'react'
import Avatar from '@mui/material/Avatar'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Divider from '@mui/material/Divider'
import IconButton from '@mui/material/IconButton'
import List from '@mui/material/List'
import ListItemButton from '@mui/material/ListItemButton'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import AddIcon from '@mui/icons-material/Add'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline'
import LaunchIcon from '@mui/icons-material/Launch'
import LinkOutlinedIcon from '@mui/icons-material/LinkOutlined'

import { ConfirmDialog } from '../components/ConfirmDialog'
import { PageScaffold } from '../components/PageScaffold'
import { StateBlock } from '../components/StateBlock'
import { useTranslate } from '../i18n'
import { colorVar } from '../theme/material-you'
import { bridge, errorMessage } from '../utils/bridge'
import { useAsync } from '../utils/hooks'
import type { FriendItem } from '@shared/ipc'

interface Draft {
  id: number | null
  name: string
  url: string
  avatar_url: string
  description: string
  sort: string
}

const EMPTY_DRAFT: Draft = { id: null, name: '', url: '', avatar_url: '', description: '', sort: '0' }

function toDraft(item: FriendItem): Draft {
  return {
    id: item.id,
    name: item.name,
    url: item.url,
    avatar_url: item.avatar_url ?? '',
    description: item.description ?? '',
    sort: String(item.sort)
  }
}

export function FriendsPage(): ReactNode {
  const t = useTranslate()
  const list = useAsync(() => bridge.friend.list(), [])
  const [draft, setDraft] = useState<Draft>(EMPTY_DRAFT)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [confirming, setConfirming] = useState(false)

  const items = useMemo(() => list.data ?? [], [list.data])

  useEffect(() => {
    if (items.length > 0 && draft.id === null && !draft.name && !draft.url) {
      setDraft(toDraft(items[0]))
    }
  }, [items, draft.id, draft.name, draft.url])

  const save = async (): Promise<void> => {
    setBusy(true)
    setError(null)
    try {
      const payload = {
        name: draft.name.trim(),
        url: draft.url.trim(),
        avatar_url: draft.avatar_url.trim() || null,
        description: draft.description.trim() || null,
        sort: Number.parseInt(draft.sort, 10) || 0
      }
      if (draft.id === null) {
        const created = await bridge.friend.create(payload)
        setDraft(toDraft(created))
      } else {
        const updated = await bridge.friend.update(draft.id, payload)
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
      await bridge.friend.remove(draft.id)
      setDraft(EMPTY_DRAFT)
      setConfirming(false)
      list.reload()
    } catch (caught) {
      setError(errorMessage(caught))
    } finally {
      setBusy(false)
    }
  }

  const canSave = draft.name.trim().length > 0 && draft.url.trim().length > 0

  return (
    <PageScaffold
      page="friends"
      title={t('nav.friends')}
      actions={
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="tonal" startIcon={<AddIcon />} onClick={() => setDraft(EMPTY_DRAFT)}>
            {t('friends.new')}
          </Button>
          <Button variant="contained" onClick={() => void save()} disabled={busy || !canSave}>
            {t('common.save')}
          </Button>
        </Box>
      }
    >
      <Box sx={{ display: 'flex', gap: 2, minHeight: 0, flexGrow: 1 }}>
        <Box
          sx={{
            width: 320,
            flexShrink: 0,
            borderRadius: 4,
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
            emptyText={t('friends.empty')}
            onRetry={list.reload}
          >
            <List dense disablePadding>
              {items.map((item) => (
                <ListItemButton
                  key={item.id}
                  selected={draft.id === item.id}
                  onClick={() => setDraft(toDraft(item))}
                  sx={{ gap: 1.5, py: 1, mb: 0.5 }}
                >
                  <Avatar src={item.avatar_url ?? undefined} sx={{ width: 32, height: 32 }}>
                    <LinkOutlinedIcon fontSize="small" />
                  </Avatar>
                  <Box sx={{ minWidth: 0 }}>
                    <Typography variant="body2" sx={{ fontWeight: 500 }} noWrap>
                      {item.name}
                    </Typography>
                    <Typography variant="caption" sx={{ color: colorVar('on-surface-variant') }} noWrap>
                      {item.url}
                    </Typography>
                  </Box>
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
            borderRadius: 4,
            backgroundColor: colorVar('surface-container-low'),
            border: `1px solid ${colorVar('outline-variant')}`,
            overflow: 'hidden'
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', px: 2, height: 48 }}>
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              {draft.id === null ? t('friends.new') : t('common.edit')}
            </Typography>
            {draft.url ? (
              <IconButton
                aria-label={t('friends.visit')}
                onClick={() => window.open(draft.url, '_blank')}
                sx={{ color: colorVar('primary') }}
              >
                <LaunchIcon fontSize="small" />
              </IconButton>
            ) : null}
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

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, p: 2 }}>
            <TextField
              label={t('friends.name')}
              value={draft.name}
              onChange={(event) => setDraft({ ...draft, name: event.target.value })}
              fullWidth
            />
            <TextField
              label={t('friends.url')}
              value={draft.url}
              onChange={(event) => setDraft({ ...draft, url: event.target.value })}
              fullWidth
            />
            <TextField
              label={t('friends.avatar')}
              value={draft.avatar_url}
              onChange={(event) => setDraft({ ...draft, avatar_url: event.target.value })}
              fullWidth
            />
            <TextField
              label={t('friends.description')}
              value={draft.description}
              onChange={(event) => setDraft({ ...draft, description: event.target.value })}
              multiline
              minRows={3}
              fullWidth
            />
            <TextField
              label={t('friends.sort')}
              type="number"
              value={draft.sort}
              onChange={(event) => setDraft({ ...draft, sort: event.target.value })}
              sx={{ maxWidth: 160 }}
            />
            {draft.avatar_url ? (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <Avatar src={draft.avatar_url} sx={{ width: 40, height: 40 }} />
                <Typography variant="caption" sx={{ color: colorVar('on-surface-variant') }}>
                  {t('friends.avatar')}
                </Typography>
              </Box>
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
        title={t('friends.delete_confirm')}
        destructive
        confirmLabel={t('common.delete')}
        onConfirm={() => void remove()}
        onCancel={() => setConfirming(false)}
      />
    </PageScaffold>
  )
}
