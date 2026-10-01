import { create } from 'zustand'

import type { PageId } from '../navigation'

interface ShellState {
  page: PageId
  setPage: (page: PageId) => void
}

export const useShell = create<ShellState>((set) => ({
  page: 'settings',
  setPage: (page) => set({ page })
}))
