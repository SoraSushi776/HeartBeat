import type { ReactNode } from 'react'
import type { SxProps } from '@mui/material'
import { useState } from 'react'
import Box from '@mui/material/Box'
import ButtonBase from '@mui/material/ButtonBase'
import Collapse from '@mui/material/Collapse'
import Typography from '@mui/material/Typography'
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown'

import { colorVar } from '../theme/material-you'

interface SectionCardProps {
  title: string
  hint?: string
  action?: ReactNode
  collapsible?: boolean
  defaultOpen?: boolean
  fill?: boolean
  sx?: SxProps
  children: ReactNode
}

export function SectionCard({
  title,
  hint,
  action,
  collapsible = false,
  defaultOpen = true,
  fill = false,
  sx,
  children
}: SectionCardProps): ReactNode {
  const [open, setOpen] = useState(defaultOpen)

  const header = (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Box sx={{ flexGrow: 1, minWidth: 0 }}>
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
      {collapsible ? (
        <KeyboardArrowDownIcon
          fontSize="small"
          sx={{
            color: colorVar('on-surface-variant'),
            transition: 'transform 200ms ease',
            transform: open ? 'rotate(0deg)' : 'rotate(-90deg)'
          }}
        />
      ) : null}
    </Box>
  )

  return (
    <Box
      sx={[
        {
          borderRadius: 'var(--md-sys-shape-corner-large)',
          backgroundColor: colorVar('surface-container-low'),
          border: `1px solid ${colorVar('outline-variant')}`,
          ...(fill ? { display: 'flex', flexDirection: 'column', flexGrow: 1, minHeight: 0 } : {})
        },
        ...(Array.isArray(sx) ? sx : [sx])
      ]}
    >
      {collapsible ? (
        <ButtonBase
          onClick={() => setOpen((value) => !value)}
          focusRipple
          sx={{
            width: '100%',
            px: 2,
            pt: 2,
            pb: open ? 0 : 2,
            borderRadius: 'var(--md-sys-shape-corner-large)',
            textAlign: 'left',
            display: 'block',
            flexShrink: 0
          }}
        >
          {header}
        </ButtonBase>
      ) : (
        <Box sx={{ px: 2, pt: 2, flexShrink: 0 }}>{header}</Box>
      )}
      <Collapse in={open || !collapsible} unmountOnExit={collapsible} sx={fill ? { flexGrow: 1, minHeight: 0 } : undefined}>
        <Box
          sx={{
            px: 2,
            pt: 1.5,
            pb: 2,
            display: 'flex',
            flexDirection: 'column',
            gap: 1.5,
            ...(fill ? { flexGrow: 1, minHeight: 0, overflowY: 'auto' } : {})
          }}
        >
          {children}
        </Box>
      </Collapse>
    </Box>
  )
}
