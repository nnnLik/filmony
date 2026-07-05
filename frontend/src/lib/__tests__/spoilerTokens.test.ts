import { describe, expect, it } from 'vitest'

import {
  SPOILER_CLOSE,
  SPOILER_OPEN,
  splitTextWithSpoilers,
  toggleSpoilerAtSelection,
} from '../spoilerTokens'

describe('splitTextWithSpoilers', () => {
  it('splits plain and spoiler parts', () => {
    const text = `hello ${SPOILER_OPEN}secret${SPOILER_CLOSE}!`
    expect(splitTextWithSpoilers(text)).toEqual([
      { type: 'plain', value: 'hello ', rangeStart: 0, rangeEnd: 6 },
      {
        type: 'spoiler',
        value: 'secret',
        rangeStart: 6,
        rangeEnd: 6 + SPOILER_OPEN.length + 6 + SPOILER_CLOSE.length,
      },
      {
        type: 'plain',
        value: '!',
        rangeStart: 6 + SPOILER_OPEN.length + 6 + SPOILER_CLOSE.length,
        rangeEnd: text.length,
      },
    ])
  })
})

describe('toggleSpoilerAtSelection', () => {
  it('wraps selected text', () => {
    const value = 'abc secret xyz'
    const result = toggleSpoilerAtSelection(value, 4, 10, 100)
    expect(result).toEqual({
      nextValue: `abc ${SPOILER_OPEN}secret${SPOILER_CLOSE} xyz`,
      caret: 4 + SPOILER_OPEN.length + 6 + SPOILER_CLOSE.length,
    })
  })

  it('unwraps selection inside spoiler markers', () => {
    const wrapped = `abc ${SPOILER_OPEN}secret${SPOILER_CLOSE} xyz`
    const start = 4 + SPOILER_OPEN.length
    const end = start + 6
    const result = toggleSpoilerAtSelection(wrapped, start, end, 100)
    expect(result).toEqual({ nextValue: 'abc secret xyz', caret: 10 })
  })

  it('inserts placeholder when selection is empty', () => {
    const result = toggleSpoilerAtSelection('hello', 5, 5, 100)
    expect(result?.nextValue).toBe(`hello${SPOILER_OPEN}спойлер${SPOILER_CLOSE}`)
    expect(result?.caret).toBe(5 + SPOILER_OPEN.length + 'спойлер'.length)
  })
})
