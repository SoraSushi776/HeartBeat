import type { ReactNode } from 'react'
import { useEffect } from 'react'

import { useShell } from './store'

export function useHeaderActions(actions: ReactNode | null): void {
  const setActions = useShell((state) => state.setActions)
  useEffect(() => {
    setActions(actions)
    return () => setActions(null)
  }, [actions, setActions])
}
