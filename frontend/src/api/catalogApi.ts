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
 * GET /api/catalog/search — после trim: фильмы (kinopoisk) ≥ 3 символов, игры (rawg) ≥ 4.
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
  sp.set('q', params.q.trim())
  sp.set('page', String(params.page ?? 1))
  sp.set('limit', String(params.limit ?? 15))
  return apiJson<CatalogSearchResponse>(`/api/catalog/search?${sp.toString()}`, {
    signal: params.signal,
  })
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
