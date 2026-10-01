import type { ReactNode } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'

import { colorVar } from '../theme/material-you'

interface FieldRowProps {
  label: string
  hint?: string
  control: ReactNode
}

export function FieldRow({ label, hint, control }: FieldRowProps): ReactNode {
  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: { xs: '1fr', sm: '220px 1fr' },
        gap: { xs: 0.5, sm: 2 },
        alignItems: 'center'
      }}
    >
      <Box>
        <Typography variant="body2" sx={{ color: colorVar('on-surface') }}>
          {label}
        </Typography>
        {hint ? (
          <Typography variant="caption" sx={{ color: colorVar('on-surface-variant'), display: 'block' }}>
            {hint}
          </Typography>
        ) : null}
      </Box>
      <Box sx={{ minWidth: 0, display: 'flex', alignItems: 'center', gap: 1.5 }}>{control}</Box>
    </Box>
  )
}
