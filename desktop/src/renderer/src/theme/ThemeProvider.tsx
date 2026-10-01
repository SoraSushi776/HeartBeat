import CssBaseline from '@mui/material/CssBaseline'
import { ThemeProvider as MuiThemeProvider } from '@mui/material/styles'
import useMediaQuery from '@mui/material/useMediaQuery'
import { useEffect, useMemo, type ReactNode } from 'react'

import { applyTokens, buildScheme, buildTokens } from './material-you'
import { useThemePreference } from './preferences'
import { createMaterialYouTheme } from './theme'

export function useResolvedMode(): 'light' | 'dark' {
  const mode = useThemePreference((state) => state.mode)
  const prefersDark = useMediaQuery('(prefers-color-scheme: dark)')
  if (mode === 'system') {
    return prefersDark ? 'dark' : 'light'
  }
  return mode
}

export function MaterialYouProvider({ children }: { children: ReactNode }): ReactNode {
  const { seed, variant, contrast } = useThemePreference()
  const mode = useResolvedMode()

  const scheme = useMemo(
    () => buildScheme({ seed, dark: mode === 'dark', variant, contrast }),
    [seed, mode, variant, contrast]
  )

  useEffect(() => {
    const root = document.documentElement
    applyTokens(root, buildTokens({ seed, dark: mode === 'dark', variant, contrast }))
    root.style.colorScheme = mode
  }, [seed, mode, variant, contrast])

  const theme = useMemo(() => createMaterialYouTheme(mode, scheme), [mode, scheme])

  return (
    <MuiThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </MuiThemeProvider>
  )
}
