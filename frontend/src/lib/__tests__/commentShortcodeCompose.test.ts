import { describe, expect, it } from 'vitest'

import { applyMentionPick } from '../feedMentionCompose'
import { parseActiveShortcodeQuery } from '../commentShortcodeCompose'
import { reactionTokenFromShortcode } from '../commentReactionTokens'

describe('parseActiveShortcodeQuery', () => {
  it('returns empty query after a colon at the start', () => {
    expect(parseActiveShortcodeQuery(':', 1)).toEqual({ colonIndex: 0, query: '' })
  })

  it('returns empty query after a colon following whitespace', () => {
    expect(parseActiveShortcodeQuery('hello :', 7)).toEqual({ colonIndex: 6, query: '' })
  })

  it('returns the letters after the last colon before the caret', () => {
    expect(parseActiveShortcodeQuery(':ga', 3)).toEqual({ colonIndex: 0, query: 'ga' })
  })

  it('does not open after 10:30 time-like text', () => {
    expect(parseActiveShortcodeQuery('10:30', 5)).toBeNull()
  })

  it('does not open after a word-colon like hello:', () => {
    expect(parseActiveShortcodeQuery('hello:', 6)).toBeNull()
  })

  it('does not reopen after a completed :gasp: token', () => {
    expect(parseActiveShortcodeQuery(':gasp:', 6)).toBeNull()
  })

  it('returns null when the query contains a space', () => {
    expect(parseActiveShortcodeQuery(':ga ', 4)).toBeNull()
  })

  it('returns null when a non-empty query starts with a digit', () => {
    expect(parseActiveShortcodeQuery(':1abc', 5)).toBeNull()
  })

  it('returns null when a non-empty query has uppercase letters', () => {
    expect(parseActiveShortcodeQuery(':Gasp', 5)).toBeNull()
  })
})

describe('applyMentionPick with shortcode tokens', () => {
  it('replaces :ga with :gasp: at the caret', () => {
    const token = reactionTokenFromShortcode('gasp')
    const res = applyMentionPick(':ga', 3, 0, token)
    expect(res).toEqual({ nextValue: ':gasp:', caret: 6 })
  })
})
