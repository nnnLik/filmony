import { normalizeCatalogSearchQuery } from '../lib/normalizeCatalogSearchQuery'
import { apiJson } from './client'
import type { Film, UserCardProvider } from './profileTypes'

/** GET /api/catalog/search — только провайдеры с поиском (без `no_provider`). */
export type CatalogSearchProvider = Extract<UserCardProvider, 'kinopoisk' | 'rawg'>

export type CatalogSearchHitKind = 'film' | 'game'

export type CatalogSearchHitSource = 'local' | 'remote'

export type CatalogSearchHit = {
  provider: Extract<UserCardProvider, 'kinopoisk' | 'rawg'>
  external_id: string
  kind: CatalogSearchHitKind
  title: string
  subtitle: string | null
  cover_url: string | null
  catalog_item_id: number | null
  source: CatalogSearchHitSource
}

export type CatalogSearchResponse = {
  items: CatalogSearchHit[]
  has_more: boolean
}

export type CatalogCandidateKind = 'film' | 'game'

export type CatalogCandidateSource = 'local' | 'remote'

export type CatalogCandidate = {
  candidate_id: string
  provider: UserCardProvider
  external_id: string
  kind: CatalogCandidateKind
  kind_hint?: CatalogCandidateKind | null
  title: string
  subtitle: string | null
  cover_url: string | null
  catalog_item_id: number | null
  source: CatalogCandidateSource
  degraded?: boolean | null
}

export type CatalogCandidatesMeta = {
  degraded_sources: string[]
}

export type CatalogCandidatesResponse = {
  items: CatalogCandidate[]
  has_more: boolean
  meta: CatalogCandidatesMeta
}

/** POST /api/catalog/resolve-by-url — provider определяется по host URL на сервере. */
export type CatalogResolveByUrlResponse = {
  catalog_item_id: number
  provider: UserCardProvider
  external_id: string
  kind: 'film'
  title: string
  cover_url: string | null
  summary: string | null
  film: Film
}

/** Разрешённые значения `provider` в теле POST /api/catalog/resolve (сервер отклоняет `no_provider`). */
export type CatalogResolveRequestProvider = Extract<UserCardProvider, 'kinopoisk'>

/** POST /api/catalog/resolve — пара `{ provider, url }`; с клиента передаём только `kinopoisk`. */
export type CatalogResolveResponse = {
  catalog_item_id: number
  provider: UserCardProvider
  external_id: string
  title: string
  cover_url: string | null
  summary: string | null
  film: Film
}

export async function resolveCatalogByProviderUrl(
  provider: CatalogResolveRequestProvider,
  url: string,
): Promise<CatalogResolveResponse> {
  return apiJson<CatalogResolveResponse>('/api/catalog/resolve', {
    method: 'POST',
    body: JSON.stringify({ provider, url }),
    headers: { 'Content-Type': 'application/json' },
  })
}

/**
 * GET /api/catalog/search — после нормализации (trim, пробелы, lower): kinopoisk ≥ 3, rawg ≥ 4.
 * Передайте `signal`, чтобы отменять запрос при смене строки или размонтировании (React Query).
 */
export async function searchCatalog(params: {
  provider: CatalogSearchProvider
  q: string
  page?: number
  limit?: number
  signal?: AbortSignal
}): Promise<CatalogSearchResponse> {
  const sp = new URLSearchParams()
  sp.set('provider', params.provider)
  sp.set('q', normalizeCatalogSearchQuery(params.q))
  sp.set('page', String(params.page ?? 1))
  sp.set('limit', String(params.limit ?? 15))
  return apiJson<CatalogSearchResponse>(`/api/catalog/search?${sp.toString()}`, {
    signal: params.signal,
  })
}

/**
 * GET /api/catalog/candidates — смешанный поиск Kinopoisk + RAWG одним списком.
 * Передайте `signal`, чтобы отменять запрос при смене строки или размонтировании.
 */
export async function searchCatalogCandidates(params: {
  q: string
  page?: number
  limit?: number
  signal?: AbortSignal
}): Promise<CatalogCandidatesResponse> {
  const sp = new URLSearchParams()
  sp.set('q', normalizeCatalogSearchQuery(params.q))
  sp.set('page', String(params.page ?? 1))
  sp.set('limit', String(params.limit ?? 15))
  return apiJson<CatalogCandidatesResponse>(`/api/catalog/candidates?${sp.toString()}`, {
    signal: params.signal,
  })
}

/** POST /api/catalog/resolve-by-url — резолв каталога по URL без явного provider. */
export async function resolveCatalogByUrl(url: string): Promise<CatalogResolveByUrlResponse> {
  return apiJson<CatalogResolveByUrlResponse>('/api/catalog/resolve-by-url', {
    method: 'POST',
    body: JSON.stringify({ url: url.trim() }),
    headers: { 'Content-Type': 'application/json' },
  })
}

/** Эвристика для smart-field: ввод похож на URL, а не на текстовый поиск. */
export function isLikelyUrl(raw: string): boolean {
  const trimmed = raw.trim()
  if (trimmed === '') return false
  if (/^https?:\/\//i.test(trimmed)) return true
  try {
    const href = trimmed.includes('://') ? trimmed : `https://${trimmed}`
    const url = new URL(href)
    const host = url.hostname.toLowerCase()
    if (host === 'localhost') return true
    return host.includes('.') && !host.startsWith('.') && !host.endsWith('.')
  } catch {
    return false
  }
}

/** Возвращает slug провайдера каталога для URL или `null` (клиент использует legacy `/api/films/resolve`). */
export function inferCatalogProviderFromUrl(urlRaw: string): CatalogResolveRequestProvider | null {
  const trimmed = urlRaw.trim()
  if (trimmed === '') return null
  try {
    const href = trimmed.includes('://') ? trimmed : `https://${trimmed}`
    const url = new URL(href)
    const host = url.hostname.toLowerCase()
    if (host === 'kinopoisk.ru' || host.endsWith('.kinopoisk.ru')) {
      return 'kinopoisk'
    }
    return null
  } catch {
    return null
  }
}
