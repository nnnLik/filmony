import { useSyncExternalStore } from 'react'

/** Shared dancing-Pepe asset used by feed chrome and desktop side rails */
export const PEPE_DANCING_GIF_URL = 'https://i.gifer.com/3nRK.gif'

/**
 * Desktop side-rail disco easter egg (source page: https://gifer.com/ru/7V5).
 * Alternate header title Pepe loops this GIF whenever disco completes.
 */
export const SIDE_DISCO_RAIN_GIF_URL = 'https://i.gifer.com/7V5.gif'

const HEADER_PEPE_ALT_VARIANT_STORAGE_KEY = 'filmony.header-pepe.alt'

let preloadPromise: Promise<void> | null = null

let sideDiscoRainPreloadPromise: Promise<void> | null = null

const linkPreloadInjectedIds = new Set<string>()

function ensureLinkPreloadImage(url: string, elementId: string): void {
  if (typeof document === 'undefined') return
  if (linkPreloadInjectedIds.has(elementId)) return
  if (document.getElementById(elementId)) {
    linkPreloadInjectedIds.add(elementId)
    return
  }
  linkPreloadInjectedIds.add(elementId)
  const link = document.createElement('link')
  link.id = elementId
  link.rel = 'preload'
  link.as = 'image'
  link.href = url
  document.head.appendChild(link)
}

let headerPepeUsesAltVariant = false

let headerPepeAltHydratedFromStorage = false

const headerPepeGifListeners = new Set<() => void>()

function hydrateHeaderPepeAltFromStorageIfNeeded(): void {
  if (typeof window === 'undefined' || headerPepeAltHydratedFromStorage) {
    return
  }
  headerPepeAltHydratedFromStorage = true
  try {
    headerPepeUsesAltVariant = window.localStorage.getItem(HEADER_PEPE_ALT_VARIANT_STORAGE_KEY) === '1'
  } catch {
    headerPepeUsesAltVariant = false
  }
}

function persistHeaderPepeAltVariant(usesAlt: boolean): void {
  if (typeof window === 'undefined') {
    return
  }
  try {
    if (usesAlt) {
      window.localStorage.setItem(HEADER_PEPE_ALT_VARIANT_STORAGE_KEY, '1')
    } else {
      window.localStorage.removeItem(HEADER_PEPE_ALT_VARIANT_STORAGE_KEY)
    }
  } catch {
    /* ignore quota / privacy mode */
  }
}

function notifyHeaderPepeGifListeners(): void {
  for (const listener of headerPepeGifListeners) {
    listener()
  }
}

export function subscribeHeaderPepeGifSrc(listener: () => void): () => void {
  hydrateHeaderPepeAltFromStorageIfNeeded()
  headerPepeGifListeners.add(listener)
  return () => {
    headerPepeGifListeners.delete(listener)
  }
}

/**
 * Current URL for Feed/Search/Profile title Pepe. Derives from persisted variant
 * (default dancing vs `SIDE_DISCO_RAIN_GIF_URL`); updates once when a disco session begins.
 */
export function getHeaderPepeGifSrc(): string {
  hydrateHeaderPepeAltFromStorageIfNeeded()
  return headerPepeUsesAltVariant ? SIDE_DISCO_RAIN_GIF_URL : PEPE_DANCING_GIF_URL
}

function getServerHeaderPepeGifSrc(): string {
  return PEPE_DANCING_GIF_URL
}

/**
 * Flips header title Pepe (default ⇄ side-disco GIF), persists, notifies subscribers.
 * Invoke once when a **new** disco session starts (`discoSides` transitions off → on), not inside a `setState`
 * functional updater (React Strict Mode may run that updater twice in dev — double-invocation would negate the toggle).
 */
export function toggleHeaderPepeGifAfterDiscoCompletes(): void {
  hydrateHeaderPepeAltFromStorageIfNeeded()
  headerPepeUsesAltVariant = !headerPepeUsesAltVariant
  persistHeaderPepeAltVariant(headerPepeUsesAltVariant)
  notifyHeaderPepeGifListeners()
}

/**
 * Prefer this in React: stays in sync with disco toggles and `localStorage` without SSR mismatch.
 */
export function useHeaderPepeGifSrc(): string {
  return useSyncExternalStore(subscribeHeaderPepeGifSrc, getHeaderPepeGifSrc, getServerHeaderPepeGifSrc)
}

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

/**
 * Preloads {@link SIDE_DISCO_RAIN_GIF_URL} once; safe to call from multiple surfaces.
 */
export function ensureSideDiscoRainGifPreloaded(): Promise<void> {
  if (typeof window === 'undefined') return Promise.resolve()
  sideDiscoRainPreloadPromise ??= new Promise<void>((resolve) => {
    const img = new Image()
    img.onload = () => resolve()
    img.onerror = () => resolve()
    img.src = SIDE_DISCO_RAIN_GIF_URL
  })
  return sideDiscoRainPreloadPromise
}

/** Preloads both GIFs referenced by header title Pepe (either variant may show). */
export function ensureHeaderPepeGifsPreloaded(): Promise<void> {
  return Promise.all([
    ensurePepeDancingGifPreloaded(),
    ensureSideDiscoRainGifPreloaded(),
  ]).then(() => undefined)
}

/**
 * Starts fetch + decode pipeline as early as possible: `<link rel="preload" as="image">`
 * for both header/side GIFs (deduped) plus the existing in-memory `Image()` preloads.
 * Safe to call from layout and from feed/search/profile surfaces.
 */
export function prewarmAllPepeDiscoAssets(): Promise<void> {
  if (typeof window === 'undefined') return Promise.resolve()
  ensureLinkPreloadImage(PEPE_DANCING_GIF_URL, 'filmony-preload-pepe-dancing-gif')
  ensureLinkPreloadImage(SIDE_DISCO_RAIN_GIF_URL, 'filmony-preload-side-disco-rain-gif')
  return ensureHeaderPepeGifsPreloaded()
}
