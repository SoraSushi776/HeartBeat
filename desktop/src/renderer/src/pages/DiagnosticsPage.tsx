import type { ReactNode } from 'react'
import { useEffect, useMemo, useState } from 'react'
import Avatar from '@mui/material/Avatar'
import Box from '@mui/material/Box'
import Chip from '@mui/material/Chip'
import LinearProgress from '@mui/material/LinearProgress'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemText from '@mui/material/ListItemText'
import Typography from '@mui/material/Typography'
import GraphicEqOutlinedIcon from '@mui/icons-material/GraphicEqOutlined'
import MusicOffOutlinedIcon from '@mui/icons-material/MusicOffOutlined'

import { PageScaffold } from '../components/PageScaffold'
import { useHeaderActions } from '../shell/header'
import { SectionCard } from '../components/SectionCard'
import { StateBlock } from '../components/StateBlock'
import { useLanguage, useTranslate } from '../i18n'
import { colorVar } from '../theme/material-you'
import { bridge } from '../utils/bridge'
import { formatDuration, formatRelative } from '../utils/format'
import { useAsync, useInterval } from '../utils/hooks'
import type { PushRecordView, SnapshotView } from '@shared/ipc'

const REFRESH_MS = 5000

export function DiagnosticsPage(): ReactNode {
  const t = useTranslate()
  const language = useLanguage((state) => state.language)
  const [snapshot, setSnapshot] = useState<SnapshotView | null>(null)
  const [history, setHistory] = useState<PushRecordView[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [nonce, setNonce] = useState(0)

  const historyQuery = useAsync(() => bridge.diagnostics.history(), [])

  useEffect(() => {
    if (historyQuery.data) {
      setHistory(historyQuery.data)
    }
  }, [historyQuery.data])

  useEffect(() => {
    const unsubscribe = bridge.diagnostics.onPushResult((record) => {
      setHistory((current) => [record, ...current].slice(0, 20))
    })
    return unsubscribe
  }, [])

  useEffect(() => {
    let active = true
    const load = async (): Promise<void> => {
      try {
        const next = await bridge.diagnostics.snapshot()
        if (active) {
          setSnapshot(next)
          setError(null)
        }
      } catch (caught) {
        if (active) {
          setError(caught instanceof Error ? caught.message : String(caught))
        }
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }
    void load()
    return () => {
      active = false
    }
  }, [nonce])

  useInterval(() => setNonce((value) => value + 1), REFRESH_MS)

  const headerActions = useMemo(
    () => (
      <Typography variant="caption" sx={{ color: colorVar('on-surface-variant') }}>
        {t('diagnostics.auto_refresh')}
      </Typography>
    ),
    [t]
  )
  useHeaderActions(headerActions)

  const media = snapshot?.media ?? null
  const system = snapshot?.system ?? null

  return (
    <PageScaffold>
      <StateBlock loading={loading} error={error} onRetry={() => setNonce((value) => value + 1)}>
        <SectionCard title={t('diagnostics.media')}>
          {media && media.state !== 'idle' ? (
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <Avatar
                variant="rounded"
                src={snapshot?.coverDataUrl ?? undefined}
                sx={{ width: 72, height: 72, borderRadius: '12px', backgroundColor: colorVar('surface-container-highest') }}
              >
                <GraphicEqOutlinedIcon />
              </Avatar>
              <Box sx={{ minWidth: 0, flexGrow: 1 }}>
                <Typography variant="h5" noWrap>
                  {media.title ?? t('common.unknown')}
                </Typography>
                <Typography variant="body2" sx={{ color: colorVar('on-surface-variant') }} noWrap>
                  {[media.artist, media.album].filter(Boolean).join(' · ') || t('common.unknown')}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                  <Chip
                    size="small"
                    label={media.app ?? t('common.unknown')}
                    sx={{ borderColor: colorVar('outline') }}
                  />
                  <Chip
                    size="small"
                    label={media.state}
                    sx={{
                      backgroundColor: colorVar('secondary-container'),
                      color: colorVar('on-secondary-container'),
                      border: 'none'
                    }}
                  />
                  <Typography variant="caption" sx={{ color: colorVar('on-surface-variant') }}>
                    {formatDuration(media.position_ms)} / {formatDuration(media.duration_ms)}
                  </Typography>
                </Box>
                {media.duration_ms && media.duration_ms > 0 ? (
                  <LinearProgress
                    variant="determinate"
                    value={Math.min(((media.position_ms ?? 0) / media.duration_ms) * 100, 100)}
                    sx={{ mt: 1 }}
                  />
                ) : null}
              </Box>
            </Box>
          ) : (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, py: 1 }}>
              <MusicOffOutlinedIcon sx={{ color: colorVar('on-surface-variant') }} />
              <Typography variant="body2" sx={{ color: colorVar('on-surface-variant') }}>
                {t('diagnostics.idle')}
              </Typography>
            </Box>
          )}
        </SectionCard>

        <SectionCard title={t('diagnostics.system')}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Metric
              label={t('diagnostics.cpu')}
              value={system?.cpu_percent ?? 0}
              suffix="%"
            />
            <Metric
              label={t('diagnostics.memory')}
              value={system?.memory_percent ?? 0}
              suffix="%"
            />
            <Box>
              <Typography variant="body2" sx={{ color: colorVar('on-surface-variant') }}>
                {t('diagnostics.load')}
              </Typography>
              <Typography variant="body1">
                {system && system.load_avg.length > 0
                  ? system.load_avg.map((value) => value.toFixed(2)).join('  ')
                  : t('diagnostics.load_unavailable')}
              </Typography>
            </Box>
          </Box>
        </SectionCard>

        <SectionCard title={t('diagnostics.history')}>
          {history.length === 0 ? (
            <Typography variant="body2" sx={{ color: colorVar('on-surface-variant') }}>
              {t('diagnostics.history_empty')}
            </Typography>
          ) : (
            <List dense disablePadding>
              {history.map((record, index) => (
                <ListItem key={`${record.ts}-${index}`} disableGutters sx={{ py: 0.5 }}>
                  <Box
                    sx={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      mr: 1.5,
                      flexShrink: 0,
                      backgroundColor: record.ok ? colorVar('primary') : colorVar('error')
                    }}
                  />
                  <ListItemText
                    primary={record.ok ? t('diagnostics.push_ok') : t('diagnostics.push_failed')}
                    secondary={`${formatRelative(record.ts, language)} · ${record.detail}`}
                    slotProps={{ secondary: { noWrap: true } }}
                  />
                </ListItem>
              ))}
            </List>
          )}
        </SectionCard>

        {snapshot ? (
          <Typography variant="caption" sx={{ color: colorVar('on-surface-variant') }}>
            {t('diagnostics.collected_at')} {formatRelative(snapshot.collectedAt, language)}
          </Typography>
        ) : null}
      </StateBlock>
    </PageScaffold>
  )
}

function Metric({ label, value, suffix }: { label: string; value: number; suffix: string }): ReactNode {
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
        <Typography variant="body2" sx={{ color: colorVar('on-surface-variant') }}>
          {label}
        </Typography>
        <Typography variant="body2">
          {value.toFixed(1)}
          {suffix}
        </Typography>
      </Box>
      <LinearProgress variant="determinate" value={Math.min(value, 100)} sx={{ mt: 0.5 }} />
    </Box>
  )
}
