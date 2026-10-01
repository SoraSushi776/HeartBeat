import type { ReactNode } from 'react'
import Box from '@mui/material/Box'
import IconButton from '@mui/material/IconButton'
import Menu from '@mui/material/Menu'
import MenuItem from '@mui/material/MenuItem'
import Typography from '@mui/material/Typography'
import Tooltip from '@mui/material/Tooltip'
import CheckIcon from '@mui/icons-material/Check'
import PaletteOutlinedIcon from '@mui/icons-material/PaletteOutlined'
import TranslateIcon from '@mui/icons-material/Translate'
import { useState } from 'react'

import { LANGUAGES, useLanguage, useTranslate } from '../i18n'
import { DESTINATIONS, type PageId } from '../navigation'
import { SEED_PRESETS, colorVar, type SchemeVariant } from '../theme/material-you'
import { useThemePreference, type ThemeMode } from '../theme/preferences'

const MODES: { value: ThemeMode; key: 'appearance.mode.system' | 'appearance.mode.light' | 'appearance.mode.dark' }[] = [
  { value: 'system', key: 'appearance.mode.system' },
  { value: 'light', key: 'appearance.mode.light' },
  { value: 'dark', key: 'appearance.mode.dark' }
]

const CONTRASTS: { value: number; key: 'appearance.contrast.standard' | 'appearance.contrast.medium' | 'appearance.contrast.high' }[] = [
  { value: 0, key: 'appearance.contrast.standard' },
  { value: 0.5, key: 'appearance.contrast.medium' },
  { value: 1, key: 'appearance.contrast.high' }
]

const VARIANTS: SchemeVariant[] = ['tonalSpot', 'vibrant', 'expressive', 'content', 'neutral', 'monochrome']

interface AppTopBarProps {
  page: PageId
  isMac: boolean
}

export function AppTopBar({ page, isMac }: AppTopBarProps): ReactNode {
  const t = useTranslate()
  const mode = useThemePreference((state) => state.mode)
  const seed = useThemePreference((state) => state.seed)
  const variant = useThemePreference((state) => state.variant)
  const contrast = useThemePreference((state) => state.contrast)
  const setMode = useThemePreference((state) => state.setMode)
  const setSeed = useThemePreference((state) => state.setSeed)
  const setVariant = useThemePreference((state) => state.setVariant)
  const setContrast = useThemePreference((state) => state.setContrast)
  const language = useLanguage((state) => state.language)
  const setLanguage = useLanguage((state) => state.setLanguage)
  const [appearanceAnchor, setAppearanceAnchor] = useState<null | HTMLElement>(null)
  const [languageAnchor, setLanguageAnchor] = useState<null | HTMLElement>(null)

  const destination = DESTINATIONS.find((item) => item.id === page)

  const sectionLabel = (text: string): ReactNode => (
    <MenuItem disabled sx={{ '&.Mui-disabled': { opacity: 1 }, fontWeight: 500, fontSize: 12, letterSpacing: '0.5px' }}>
      {text}
    </MenuItem>
  )

  return (
    <Box
      className="app-drag-region"
      sx={{
        height: 'var(--md-sys-top-bar-height)',
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        pl: isMac ? 10 : 2,
        pr: 2,
        backgroundColor: colorVar('surface')
      }}
    >
      <Typography variant="h5" sx={{ flexGrow: 1 }}>
        {destination ? t(destination.labelKey) : t('app.name')}
      </Typography>

      <Box className="app-no-drag" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Tooltip title={t('appearance.title')}>
          <IconButton
            onClick={(event) => setAppearanceAnchor(event.currentTarget)}
            aria-label={t('appearance.title')}
            sx={{ backgroundColor: colorVar('surface-container-high') }}
          >
            <PaletteOutlinedIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title={t('language.title')}>
          <IconButton onClick={(event) => setLanguageAnchor(event.currentTarget)} aria-label={t('language.title')}>
            <TranslateIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>

      <Menu
        anchorEl={appearanceAnchor}
        open={Boolean(appearanceAnchor)}
        onClose={() => setAppearanceAnchor(null)}
        slotProps={{ list: { sx: { minWidth: 240 } } }}
      >
        {sectionLabel(t('appearance.mode'))}
        {MODES.map((item) => (
          <MenuItem key={item.value} onClick={() => setMode(item.value)}>
            <Box sx={{ flexGrow: 1 }}>{t(item.key)}</Box>
            {mode === item.value ? <CheckIcon fontSize="small" /> : null}
          </MenuItem>
        ))}
        {sectionLabel(t('appearance.seed'))}
        {SEED_PRESETS.map((preset) => (
          <MenuItem key={preset.value} onClick={() => setSeed(preset.value)}>
            <Box
              sx={{
                width: 18,
                height: 18,
                borderRadius: '50%',
                backgroundColor: preset.value,
                mr: 1.5,
                border: `1px solid ${colorVar('outline-variant')}`
              }}
            />
            <Box sx={{ flexGrow: 1 }}>{preset.label}</Box>
            {seed.toLowerCase() === preset.value.toLowerCase() ? <CheckIcon fontSize="small" /> : null}
          </MenuItem>
        ))}
        {sectionLabel(t('appearance.variant'))}
        {VARIANTS.map((item) => (
          <MenuItem key={item} onClick={() => setVariant(item)}>
            <Box sx={{ flexGrow: 1 }}>{item}</Box>
            {variant === item ? <CheckIcon fontSize="small" /> : null}
          </MenuItem>
        ))}
        {sectionLabel(t('appearance.contrast'))}
        {CONTRASTS.map((item) => (
          <MenuItem key={item.value} onClick={() => setContrast(item.value)}>
            <Box sx={{ flexGrow: 1 }}>{t(item.key)}</Box>
            {contrast === item.value ? <CheckIcon fontSize="small" /> : null}
          </MenuItem>
        ))}
      </Menu>

      <Menu anchorEl={languageAnchor} open={Boolean(languageAnchor)} onClose={() => setLanguageAnchor(null)}>
        {LANGUAGES.map((item) => (
          <MenuItem
            key={item.value}
            onClick={() => {
              setLanguage(item.value)
              setLanguageAnchor(null)
            }}
          >
            <Box sx={{ flexGrow: 1 }}>{t(item.labelKey)}</Box>
            {language === item.value ? <CheckIcon fontSize="small" /> : null}
          </MenuItem>
        ))}
      </Menu>
    </Box>
  )
}
