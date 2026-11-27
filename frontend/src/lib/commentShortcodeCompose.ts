import type { ReactionCatalogItem, ReactionGroupedCatalog } from '../api/profileTypes'
import { applyMentionPick } from './feedMentionCompose'

export type ActiveShortcodeQuery = {
  colonIndex: number
  query: string
}

export const SHORTCODE_SUGGEST_LIMIT = 24

const QUERY_RE = /^[a-z][a-z0-9_+-]*$/
const CHAR_BEFORE_COLON_RE = /[a-zA-Z0-9_+-]/

/**
 * If the caret is immediately after `:` and an optional shortcode query (composer only),
 * returns the span to replace with `:shortcode:`.
 */
export function parseActiveShortcodeQuery(value: string, caret: number): ActiveShortcodeQuery | null {
  if (caret < 1 || caret > value.length) {
    return null
  }
  const before = value.slice(0, caret)
  const colonIndex = before.lastIndexOf(':')
  if (colonIndex === -1) {
    return null
  }
  if (colonIndex > 0) {
    const prev = before.charAt(colonIndex - 1)
    if (CHAR_BEFORE_COLON_RE.test(prev)) {
      return null
    }
  }
  const query = before.slice(colonIndex + 1)
  if (query.includes(' ') || query.includes('\n') || query.includes('\t') || query.includes(':')) {
    return null
  }
  if (query !== '' && !QUERY_RE.test(query)) {
    return null
  }
  return { colonIndex, query }
}

export { applyMentionPick }

export function flattenReactionCatalogItems(catalog: ReactionGroupedCatalog): ReactionCatalogItem[] {
  const seen = new Set<number>()
  const out: ReactionCatalogItem[] = []
  for (const tab of catalog.tabs) {
    for (const it of tab.items) {
      if (seen.has(it.id)) continue
      seen.add(it.id)
      out.push(it)
    }
  }
  return out
}

export function idToShortcodeMapFromCatalog(catalog: ReactionGroupedCatalog): Map<number, string> {
  const map = new Map<number, string>()
  for (const it of flattenReactionCatalogItems(catalog)) {
    if (it.shortcode !== '') {
      map.set(it.id, it.shortcode)
    }
  }
  return map
}

export function filterCatalogItemsForShortcodeQuery(
  items: readonly ReactionCatalogItem[],
  query: string,
  limit = SHORTCODE_SUGGEST_LIMIT,
): ReactionCatalogItem[] {
  const q = query.toLowerCase()
  const prefix: ReactionCatalogItem[] = []
  const substring: ReactionCatalogItem[] = []
  for (const it of items) {
    const code = it.shortcode.toLowerCase()
    if (code.startsWith(q)) {
      prefix.push(it)
    } else if (q !== '' && code.includes(q)) {
      substring.push(it)
    }
  }
  if (prefix.length >= limit) {
    return prefix.slice(0, limit)
  }
  return [...prefix, ...substring].slice(0, limit)
}
