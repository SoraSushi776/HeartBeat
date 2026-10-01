import type { ReactNode } from 'react'
import { create } from 'zustand'

import type { PageId } from '../navigation'

interface ShellState {
  page: PageId
  actions: ReactNode | null
  setPage: (page: PageId) => void
  setActions: (actions: ReactNode | null) => void
}

export const useShell = create<ShellState>((set) => ({
  page: 'settings',
  actions: null,
  setPage: (page) => set({ page }),
  setActions: (actions) => set({ actions })
}))
