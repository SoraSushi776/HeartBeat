import type { ReactNode } from 'react'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import Typography from '@mui/material/Typography'

import { useTranslate } from '../i18n'
import { colorVar } from '../theme/material-you'

interface StateBlockProps {
  loading?: boolean
  error?: string | null
  empty?: boolean
  emptyText?: string
  onRetry?: () => void
  children: ReactNode
}

export function StateBlock({
  loading,
  error,
  empty,
  emptyText,
  onRetry,
  children
}: StateBlockProps): ReactNode {
  const t = useTranslate()

  if (loading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, py: 4, justifyContent: 'center' }}>
        <CircularProgress size={18} />
        <Typography variant="body2" sx={{ color: colorVar('on-surface-variant') }}>
          {t('common.loading')}
        </Typography>
      </Box>
    )
  }

  if (error) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, alignItems: 'flex-start', py: 2 }}>
        <Typography variant="body2" sx={{ color: colorVar('error') }}>
          {error}
        </Typography>
        {onRetry ? (
          <Button variant="text" onClick={onRetry}>
            {t('common.retry')}
          </Button>
        ) : null}
      </Box>
    )
  }

  if (empty) {
    return (
      <Box sx={{ py: 4, textAlign: 'center' }}>
        <Typography variant="body2" sx={{ color: colorVar('on-surface-variant') }}>
          {emptyText ?? t('common.empty')}
        </Typography>
      </Box>
    )
  }

  return <>{children}</>
}
