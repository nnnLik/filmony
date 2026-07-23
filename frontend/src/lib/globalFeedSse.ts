import { readAccessToken } from './filmonySession'
import { resolveApiUrl } from '../api/client'

function parseSseDataLines(buffer: string): { events: { version: number }[]; rest: string } {
  const events: { version: number }[] = []
  let rest = buffer
  while (true) {
    const idx = rest.indexOf('\n\n')
    if (idx === -1) break
    const block = rest.slice(0, idx)
    rest = rest.slice(idx + 2)
    for (const line of block.split('\n')) {
      if (!line.startsWith('data:')) continue
      const payload = line.slice(5).trim()
      if (payload === '') continue
      try {
        const obj: unknown = JSON.parse(payload)
        if (typeof obj === 'object' && obj !== null && 'version' in obj) {
          const v = obj.version
          if (typeof v === 'number' && Number.isFinite(v)) {
            events.push({ version: v })
          }
        }
      } catch {
        /* ignore malformed */
      }
    }
  }
  return { events, rest }
}

/**
 * Читает SSE /api/feed/global/events до отмены сигналом.
 * Требуется Bearer (sessionStorage) или cookie-сессия на том же origin.
 */
export async function consumeGlobalFeedHeadSse(
  signal: AbortSignal,
  onVersion: (version: number) => void,
): Promise<void> {
  const headers: Record<string, string> = { Accept: 'text/event-stream' }
  const token = readAccessToken()
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  const res = await fetch(resolveApiUrl('/api/feed/global/events'), {
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
      if (done) break
      buf += dec.decode(value, { stream: true })
      const { events, rest } = parseSseDataLines(buf)
      buf = rest
      for (const e of events) {
        onVersion(e.version)
      }
    }
  } finally {
    try {
      await reader.cancel()
    } catch {
      /* stream already closed */
    }
  }
}
