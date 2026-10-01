import type { ReactNode } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'

import { useTranslate } from '../i18n'
import { DESTINATIONS, type PageId } from '../navigation'

interface PageScaffoldProps {
  page: PageId
  title: string
  actions?: ReactNode
  children?: ReactNode
}

export function PageScaffold({ page, title, actions, children }: PageScaffoldProps): ReactNode {
  const t = useTranslate()
  const destination = DESTINATIONS.find((item) => item.id === page)

  return (
    <Box
      sx={{
        flexGrow: 1,
        minHeight: 0,
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
        px: 3,
        pt: 2,
        pb: 3,
        overflow: 'hidden'
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexShrink: 0 }}>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h4">{title}</Typography>
          {destination ? (
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              {t(destination.descriptionKey)}
            </Typography>
          ) : null}
        </Box>
        {actions}
      </Box>
      <Box
        sx={{
          flexGrow: 1,
          minHeight: 0,
          overflowY: 'auto',
          overflowX: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          gap: 2
        }}
      >
        {children}
      </Box>
    </Box>
  )
}
