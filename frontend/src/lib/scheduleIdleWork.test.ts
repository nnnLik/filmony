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
    const hadIdleCallback = 'requestIdleCallback' in window
    const originalIdleCallback = hadIdleCallback
      ? window.requestIdleCallback.bind(window)
      : undefined
    // @ts-expect-error test override
    window.requestIdleCallback = undefined

    scheduleIdleWork(work, 500)
    expect(work).not.toHaveBeenCalled()

    vi.advanceTimersByTime(500)
    expect(work).toHaveBeenCalledTimes(1)

    if (hadIdleCallback && originalIdleCallback != null) {
      window.requestIdleCallback = originalIdleCallback
    } else {
      // @ts-expect-error restore missing API
      delete window.requestIdleCallback
    }
  })
})
