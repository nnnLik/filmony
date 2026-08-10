import { useEffect, useRef, useState } from 'react'

import type { WatchPartySseEvent } from '../api/watchPartyTypes'
import { consumeWatchPartySse } from '../lib/watchPartySse'

const MIN_BACKOFF_MS = 1000
const MAX_BACKOFF_MS = 8000

export function useWatchPartyEvents(
  partyId: string | null,
  enabled: boolean,
  onEvent: (event: WatchPartySseEvent) => void,
): { lastSeq: number; connected: boolean } {
  const [lastSeq, setLastSeq] = useState(0)
  const [connected, setConnected] = useState(false)
  const onEventRef = useRef(onEvent)
  const lastSeqRef = useRef(0)

  useEffect(() => {
    onEventRef.current = onEvent
  }, [onEvent])

  useEffect(() => {
    lastSeqRef.current = lastSeq
  }, [lastSeq])

  useEffect(() => {
    if (!enabled || partyId == null) {
      queueMicrotask(() => {
        setConnected(false)
      })
      return undefined
    }

    const controller = new AbortController()
    let cancelled = false
    let backoffMs = MIN_BACKOFF_MS

    const connect = async () => {
      while (!cancelled && !controller.signal.aborted) {
        setConnected(true)
        try {
          await consumeWatchPartySse(
            partyId,
            controller.signal,
            (event) => {
              lastSeqRef.current = event.seq
              setLastSeq(event.seq)
              onEventRef.current(event)
            },
            lastSeqRef.current > 0 ? lastSeqRef.current : undefined,
          )
        } catch {
          /* stream closed */
        }

        if (cancelled || controller.signal.aborted) {
          break
        }

        setConnected(false)
        await new Promise<void>((resolve) => {
          window.setTimeout(resolve, backoffMs)
        })
        backoffMs = Math.min(backoffMs * 2, MAX_BACKOFF_MS)
      }
      setConnected(false)
    }

    void connect()

    return () => {
      cancelled = true
      controller.abort()
      setConnected(false)
    }
  }, [enabled, partyId])

  return { lastSeq, connected }
}
