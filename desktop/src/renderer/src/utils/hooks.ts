import { useCallback, useEffect, useRef, useState } from 'react'

import { errorMessage } from './bridge'

export interface AsyncState<T> {
  data: T | null
  loading: boolean
  error: string | null
  reload: () => void
  setData: (value: T | null) => void
}

export function useAsync<T>(loader: () => Promise<T>, deps: unknown[] = []): AsyncState<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [nonce, setNonce] = useState(0)
  const alive = useRef(true)

  useEffect(() => {
    alive.current = true
    return () => {
      alive.current = false
    }
  }, [])

  useEffect(() => {
    let active = true
    setLoading(true)
    loader()
      .then((value) => {
        if (!active) {
          return
        }
        setData(value)
        setError(null)
      })
      .catch((caught: unknown) => {
        if (!active) {
          return
        }
        setError(errorMessage(caught))
      })
      .finally(() => {
        if (active) {
          setLoading(false)
        }
      })
    return () => {
      active = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nonce, ...deps])

  const reload = useCallback(() => setNonce((value) => value + 1), [])
  return { data, loading, error, reload, setData }
}

export function useInterval(callback: () => void, delayMs: number | null): void {
  const saved = useRef(callback)
  saved.current = callback

  useEffect(() => {
    if (delayMs === null) {
      return
    }
    const handle = setInterval(() => saved.current(), delayMs)
    return () => clearInterval(handle)
  }, [delayMs])
}
