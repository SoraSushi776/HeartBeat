import type { ReactNode } from 'react'
import Box from '@mui/material/Box'
import Card from '@mui/material/Card'
import CardContent from '@mui/material/CardContent'
import Typography from '@mui/material/Typography'

import { colorVar } from '../theme/material-you'

interface SectionCardProps {
  title: string
  hint?: string
  action?: ReactNode
  children: ReactNode
}

export function SectionCard({ title, hint, action, children }: SectionCardProps): ReactNode {
  return (
    <Card sx={{ backgroundColor: colorVar('surface-container-low') }}>
      <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, '&:last-child': { pb: 2 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h5" sx={{ color: colorVar('on-surface') }}>
              {title}
            </Typography>
            {hint ? (
              <Typography variant="caption" sx={{ color: colorVar('on-surface-variant') }}>
                {hint}
              </Typography>
            ) : null}
          </Box>
          {action}
        </Box>
        {children}
      </CardContent>
    </Card>
  )
}
