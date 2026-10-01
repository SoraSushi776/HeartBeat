import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import { DEFAULT_SEED, type SchemeVariant } from './material-you'

export type ThemeMode = 'system' | 'light' | 'dark'

export interface ThemePreference {
  mode: ThemeMode
  seed: string
  variant: SchemeVariant
  contrast: number
}

interface ThemePreferenceState extends ThemePreference {
  setMode: (mode: ThemeMode) => void
  setSeed: (seed: string) => void
  setVariant: (variant: SchemeVariant) => void
  setContrast: (contrast: number) => void
}

export const useThemePreference = create<ThemePreferenceState>()(
  persist(
    (set) => ({
      mode: 'system',
      seed: DEFAULT_SEED,
      variant: 'tonalSpot',
      contrast: 0,
      setMode: (mode) => set({ mode }),
      setSeed: (seed) => set({ seed }),
      setVariant: (variant) => set({ variant }),
      setContrast: (contrast) => set({ contrast })
    }),
    { name: 'heartbeat-theme' }
  )
)
