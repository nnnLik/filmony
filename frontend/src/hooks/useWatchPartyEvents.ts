import { useEffect, useRef, useState } from 'react'

import type { WatchPartySseEvent } from '../api/watchPartyTypes'
import { consumeWatchPartySse } from '../lib/watchPartySse'

export function useWatchPartyEvents(
  partyId: string | null,
  enabled: boolean,
  onEvent: (event: WatchPartySseEvent) => void,
): { lastSeq: number; connected: boolean } {
  const [lastSeq, setLastSeq] = useState(0)
  const [connected, setConnected] = useState(false)
  const onEventRef = useRef(onEvent)

  useEffect(() => {
    onEventRef.current = onEvent
  }, [onEvent])

  useEffect(() => {
    if (!enabled || partyId == null) {
      queueMicrotask(() => {
        setConnected(false)
      })
      return undefined
    }

    const controller = new AbortController()
    queueMicrotask(() => {
      setConnected(true)
    })

    void consumeWatchPartySse(
      partyId,
      controller.signal,
      (event) => {
        setLastSeq(event.seq)
        onEventRef.current(event)
      },
    ).finally(() => {
      setConnected(false)
    })

    return () => {
      controller.abort()
      setConnected(false)
    }
  }, [enabled, partyId])

  return { lastSeq, connected }
}
