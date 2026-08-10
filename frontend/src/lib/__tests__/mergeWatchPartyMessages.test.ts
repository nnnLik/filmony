import { describe, expect, it } from 'vitest'

import type { WatchPartyMessage } from '../../api/watchPartyTypes'
import { mergeWatchPartyMessages } from '../mergeWatchPartyMessages'

function msg(id: number, body = `m${id}`): WatchPartyMessage {
  return {
    id,
    author_user_id: 'user-1',
    body,
    created_at: '2026-08-11T00:00:00.000Z',
  }
}

describe('mergeWatchPartyMessages', () => {
  it('upserts by id and sorts ascending', () => {
    const merged = mergeWatchPartyMessages([msg(3), msg(1)], [msg(2), msg(1, 'updated')])
    expect(merged.map((m) => m.id)).toEqual([1, 2, 3])
    expect(merged.find((m) => m.id === 1)?.body).toBe('updated')
  })

  it('dedupes REST+SSE same id to one row', () => {
    const first = mergeWatchPartyMessages([], [msg(10)])
    const second = mergeWatchPartyMessages(first, [msg(10)])
    expect(second).toHaveLength(1)
    expect(second[0]?.id).toBe(10)
  })

  it('dedupes two events with same id to one row', () => {
    const merged = mergeWatchPartyMessages([msg(5)], [msg(5)])
    expect(merged).toHaveLength(1)
  })
})
