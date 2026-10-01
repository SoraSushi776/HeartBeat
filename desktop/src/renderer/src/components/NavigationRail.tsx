import type { ReactNode } from 'react'
import Box from '@mui/material/Box'
import ButtonBase from '@mui/material/ButtonBase'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'

import { useTranslate } from '../i18n'
import { DESTINATIONS, type PageId } from '../navigation'
import { colorVar, stateLayer } from '../theme/material-you'

interface NavigationRailProps {
  active: PageId
  onSelect: (page: PageId) => void
}

export function NavigationRail({ active, onSelect }: NavigationRailProps): ReactNode {
  const t = useTranslate()

  return (
    <Box
      component="nav"
      sx={{
        width: 'var(--md-sys-navigation-rail-width)',
        flexShrink: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 1.5,
        pb: 2,
        backgroundColor: colorVar('surface'),
        borderRight: `1px solid ${colorVar('outline-variant')}`
      }}
    >
      <Box className="app-drag-region" sx={{ height: 'var(--md-sys-top-bar-height)', width: '100%', flexShrink: 0 }} />
      {DESTINATIONS.map((destination) => {
        const selected = destination.id === active
        const Icon = destination.icon
        const overlay = selected ? colorVar('on-secondary-container') : colorVar('on-surface-variant')
        return (
          <Tooltip key={destination.id} title={t(destination.labelKey)} placement="right" enterDelay={600}>
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.25 }}>
              <ButtonBase
                focusRipple
                onClick={() => onSelect(destination.id)}
                aria-current={selected ? 'page' : undefined}
                sx={{
                  width: 56,
                  height: 32,
                  borderRadius: '999px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: selected ? colorVar('on-secondary-container') : colorVar('on-surface-variant'),
                  backgroundColor: selected ? colorVar('secondary-container') : 'transparent',
                  transition: 'background-color 150ms ease, color 150ms ease',
                  '&:hover': { backgroundImage: stateLayer(overlay, 0.08) }
                }}
              >
                <Icon sx={{ fontSize: 20 }} />
              </ButtonBase>
              <Typography
                variant="caption"
                sx={{
                  color: selected ? colorVar('on-surface') : colorVar('on-surface-variant'),
                  fontWeight: selected ? 600 : 400,
                  lineHeight: '16px'
                }}
              >
                {t(destination.labelKey)}
              </Typography>
            </Box>
          </Tooltip>
        )
      })}
    </Box>
  )
}
