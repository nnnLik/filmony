import { afterEach, describe, expect, it, vi } from 'vitest'

import { scheduleIdleWork } from './scheduleIdleWork'

describe('scheduleIdleWork', () => {
  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('runs work via setTimeout fallback when requestIdleCallback is unavailable', () => {
    vi.useFakeTimers()
    const work = vi.fn()
    const original = window.requestIdleCallback
    // @ts-expect-error test override
    window.requestIdleCallback = undefined

    scheduleIdleWork(work, 500)
    expect(work).not.toHaveBeenCalled()

    vi.advanceTimersByTime(500)
    expect(work).toHaveBeenCalledTimes(1)

    window.requestIdleCallback = original
  })
})
