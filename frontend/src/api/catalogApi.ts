import { apiJson } from './client'
import type { Film } from './profileTypes'

/** POST /api/catalog/resolve — пара `{ provider, url }`; первый провайдер: `kinopoisk`. */
export type CatalogResolveResponse = {
  catalog_item_id: number
  provider: string
  external_id: string
  title: string
  cover_url: string | null
  summary: string | null
  film: Film
}

export async function resolveCatalogByProviderUrl(
  provider: string,
  url: string,
): Promise<CatalogResolveResponse> {
  return apiJson<CatalogResolveResponse>('/api/catalog/resolve', {
    method: 'POST',
    body: JSON.stringify({ provider, url }),
    headers: { 'Content-Type': 'application/json' },
  })
}

/** Возвращает slug провайдера каталога для URL или `null` (клиент использует legacy `/api/films/resolve`). */
export function inferCatalogProviderFromUrl(urlRaw: string): string | null {
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
