import { readAccessToken } from './filmonySession'
import { resolveApiUrl } from '../api/client'
import type { WatchPartySseEvent } from '../api/watchPartyTypes'

function parseSseBlocks(buffer: string): { events: WatchPartySseEvent[]; rest: string } {
  const events: WatchPartySseEvent[] = []
  let rest = buffer
  while (true) {
    const idx = rest.indexOf('\n\n')
    if (idx === -1) {
      break
    }
    const block = rest.slice(0, idx)
    rest = rest.slice(idx + 2)
    for (const line of block.split('\n')) {
      if (!line.startsWith('data:')) {
        continue
      }
      const payload = line.slice(5).trim()
      if (payload === '') {
        continue
      }
      try {
        const obj = JSON.parse(payload) as {
          seq?: unknown
          type?: unknown
          payload?: unknown
        }
        const seq = obj.seq
        const type = obj.type
        if (typeof seq !== 'number' || typeof type !== 'string') {
          continue
        }
        const eventPayload = obj.payload
        events.push({
          seq,
          type: type as WatchPartySseEvent['type'],
          payload: typeof eventPayload === 'object' && eventPayload !== null
            ? (eventPayload as Record<string, unknown>)
            : {},
        })
      } catch {
        /* ignore malformed */
      }
    }
  }
  return { events, rest }
}

export async function consumeWatchPartySse(
  partyId: string,
  signal: AbortSignal,
  onEvent: (event: WatchPartySseEvent) => void,
  sinceSeq?: number,
): Promise<void> {
  const headers: Record<string, string> = { Accept: 'text/event-stream' }
  const token = readAccessToken()
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  const qs = sinceSeq != null ? `?since_seq=${sinceSeq}` : ''
  const res = await fetch(resolveApiUrl(`/api/watch-parties/${partyId}/events${qs}`), {
    method: 'GET',
    credentials: 'include',
    headers,
    signal,
  })
  if (!res.ok || res.body == null) {
    return
  }
  const reader = res.body.getReader()
  const dec = new TextDecoder()
  let buf = ''
  try {
    while (!signal.aborted) {
      const { done, value } = await reader.read()
      if (done) {
        break
      }
      buf += dec.decode(value, { stream: true })
      const { events, rest } = parseSseBlocks(buf)
      buf = rest
      for (const event of events) {
        onEvent(event)
      }
    }
  } finally {
    try {
      await reader.cancel()
    } catch {
      /* stream closed */
    }
  }
}
