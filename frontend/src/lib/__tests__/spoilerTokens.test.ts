import { describe, expect, it } from 'vitest'

import {
  PIPE_SPOILER_MARK,
  SPOILER_CLOSE,
  SPOILER_OPEN,
  splitTextWithSpoilers,
  toggleSpoilerAtSelection,
} from '../spoilerTokens'

describe('splitTextWithSpoilers', () => {
  it('splits plain and legacy spoiler parts', () => {
    const text = `hello ${SPOILER_OPEN}secret${SPOILER_CLOSE}!`
    expect(splitTextWithSpoilers(text)).toEqual([
      { type: 'plain', value: 'hello ', rangeStart: 0, rangeEnd: 6 },
      {
        type: 'spoiler',
        value: 'secret',
        rangeStart: 6,
        rangeEnd: 6 + SPOILER_OPEN.length + 6 + SPOILER_CLOSE.length,
        openMarker: SPOILER_OPEN,
        closeMarker: SPOILER_CLOSE,
      },
      {
        type: 'plain',
        value: '!',
        rangeStart: 6 + SPOILER_OPEN.length + 6 + SPOILER_CLOSE.length,
        rangeEnd: text.length,
      },
    ])
  })

  it('splits pipe spoilers', () => {
    const text = `hello ${PIPE_SPOILER_MARK}secret${PIPE_SPOILER_MARK}!`
    expect(splitTextWithSpoilers(text)).toEqual([
      { type: 'plain', value: 'hello ', rangeStart: 0, rangeEnd: 6 },
      {
        type: 'spoiler',
        value: 'secret',
        rangeStart: 6,
        rangeEnd: 6 + PIPE_SPOILER_MARK.length + 6 + PIPE_SPOILER_MARK.length,
        openMarker: PIPE_SPOILER_MARK,
        closeMarker: PIPE_SPOILER_MARK,
      },
      {
        type: 'plain',
        value: '!',
        rangeStart: 6 + PIPE_SPOILER_MARK.length + 6 + PIPE_SPOILER_MARK.length,
        rangeEnd: text.length,
      },
    ])
  })

  it('splits sequential pipe and legacy spoilers', () => {
    const text = `${PIPE_SPOILER_MARK}a${PIPE_SPOILER_MARK} then ${SPOILER_OPEN}b${SPOILER_CLOSE}`
    expect(splitTextWithSpoilers(text)).toEqual([
      {
        type: 'spoiler',
        value: 'a',
        rangeStart: 0,
        rangeEnd: PIPE_SPOILER_MARK.length + 1 + PIPE_SPOILER_MARK.length,
        openMarker: PIPE_SPOILER_MARK,
        closeMarker: PIPE_SPOILER_MARK,
      },
      {
        type: 'plain',
        value: ' then ',
        rangeStart: PIPE_SPOILER_MARK.length + 1 + PIPE_SPOILER_MARK.length,
        rangeEnd: PIPE_SPOILER_MARK.length + 1 + PIPE_SPOILER_MARK.length + ' then '.length,
      },
      {
        type: 'spoiler',
        value: 'b',
        rangeStart: PIPE_SPOILER_MARK.length + 1 + PIPE_SPOILER_MARK.length + ' then '.length,
        rangeEnd: text.length,
        openMarker: SPOILER_OPEN,
        closeMarker: SPOILER_CLOSE,
      },
    ])
  })

  it('keeps unclosed remainder as plain', () => {
    expect(splitTextWithSpoilers(`hello ${PIPE_SPOILER_MARK}secret`)).toEqual([
      { type: 'plain', value: 'hello ', rangeStart: 0, rangeEnd: 6 },
      { type: 'plain', value: `${PIPE_SPOILER_MARK}secret`, rangeStart: 6, rangeEnd: 14 },
    ])
    expect(splitTextWithSpoilers(`${SPOILER_OPEN}secret`)).toEqual([
      { type: 'plain', value: `${SPOILER_OPEN}secret`, rangeStart: 0, rangeEnd: SPOILER_OPEN.length + 6 },
    ])
  })
})

describe('toggleSpoilerAtSelection', () => {
  it('wraps selected text with pipe markers', () => {
    const value = 'abc secret xyz'
    const result = toggleSpoilerAtSelection(value, 4, 10, 100)
    expect(result).toEqual({
      nextValue: `abc ${PIPE_SPOILER_MARK}secret${PIPE_SPOILER_MARK} xyz`,
      caret: 4 + PIPE_SPOILER_MARK.length + 6 + PIPE_SPOILER_MARK.length,
    })
  })

  it('unwraps selection inside pipe markers', () => {
    const wrapped = `abc ${PIPE_SPOILER_MARK}secret${PIPE_SPOILER_MARK} xyz`
    const start = 4 + PIPE_SPOILER_MARK.length
    const end = start + 6
    const result = toggleSpoilerAtSelection(wrapped, start, end, 100)
    expect(result).toEqual({ nextValue: 'abc secret xyz', caret: 10 })
  })

  it('unwraps selection inside legacy spoiler markers', () => {
    const wrapped = `abc ${SPOILER_OPEN}secret${SPOILER_CLOSE} xyz`
    const start = 4 + SPOILER_OPEN.length
    const end = start + 6
    const result = toggleSpoilerAtSelection(wrapped, start, end, 100)
    expect(result).toEqual({ nextValue: 'abc secret xyz', caret: 10 })
  })

  it('unwraps selection that already includes pipe markers', () => {
    const wrapped = `${PIPE_SPOILER_MARK}secret${PIPE_SPOILER_MARK}`
    const result = toggleSpoilerAtSelection(wrapped, 0, wrapped.length, 100)
    expect(result).toEqual({ nextValue: 'secret', caret: 6 })
  })

  it('inserts pipe placeholder when selection is empty', () => {
    const result = toggleSpoilerAtSelection('hello', 5, 5, 100)
    expect(result?.nextValue).toBe(`hello${PIPE_SPOILER_MARK}спойлер${PIPE_SPOILER_MARK}`)
    expect(result?.caret).toBe(5 + PIPE_SPOILER_MARK.length + 'спойлер'.length)
  })
})
