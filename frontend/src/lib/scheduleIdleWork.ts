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
  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(run, { timeout: timeoutMs })
    return
  }
  window.setTimeout(run, timeoutMs)
}
