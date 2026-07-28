/**
 * Runs work when the browser is idle, with a timeout fallback for Safari / busy main thread.
 */
export function scheduleIdleWork(work: () => void, timeoutMs = 2000): void {
  if (typeof window === 'undefined') {
    return
  }
  const run = () => {
    try {
      work()
    } catch {
      /* noop */
    }
  }
  if (typeof window.requestIdleCallback === 'function') {
    window.requestIdleCallback(run, { timeout: timeoutMs })
    return
  }
  globalThis.setTimeout(run, timeoutMs)
}
