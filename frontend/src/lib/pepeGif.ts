/** Shared dancing-Pepe asset used by feed chrome and desktop side rails */
export const PEPE_DANCING_GIF_URL = 'https://i.gifer.com/3nRK.gif'

let preloadPromise: Promise<void> | null = null

/**
 * Kicks off a single in-flight preload for `PEPE_DANCING_GIF_URL`. Safe to call
 * from every surface that renders the gif; repeats return the same promise.
 */
export function ensurePepeDancingGifPreloaded(): Promise<void> {
  if (typeof window === 'undefined') return Promise.resolve()
  preloadPromise ??= new Promise<void>((resolve) => {
    const img = new Image()
    img.onload = () => resolve()
    img.onerror = () => resolve()
    img.src = PEPE_DANCING_GIF_URL
  })
  return preloadPromise
}
