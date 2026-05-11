import { mentionTokenFromProfileSlug } from './commentReactionTokens'

export { filterFollowingForMentionQuery } from './mentionFollowingFilter'

/** Caret is inside a raw `@query` segment (not yet a ⟦@slug⟧ token). */
export type ActiveMentionQuery = {
  /** Index of `@` in value */
  atIndex: number
  query: string
}

/**
 * If the caret is immediately after `@` and optional non-space query (composer only),
 * returns the span to replace with a mention token.
 */
export function parseActiveMentionQuery(value: string, caret: number): ActiveMentionQuery | null {
  if (caret < 1 || caret > value.length) {
    return null
  }
  const before = value.slice(0, caret)
  const at = before.lastIndexOf('@')
  if (at === -1) {
    return null
  }
  const afterAt = before.slice(at + 1)
  if (afterAt.includes(' ') || afterAt.includes('\n') || afterAt.includes('\t')) {
    return null
  }
  if (afterAt.includes('⟦') || afterAt.includes('⟧')) {
    return null
  }
  return { atIndex: at, query: afterAt }
}

export function applyMentionPick(
  value: string,
  caret: number,
  atIndex: number,
  token: string,
  maxLen: number,
): { nextValue: string; caret: number } | null {
  const before = value.slice(0, atIndex)
  const after = value.slice(caret)
  const nextValue = `${before}${token}${after}`
  if (nextValue.length > maxLen) {
    return null
  }
  return { nextValue, caret: atIndex + token.length }
}

/** Canonical ⟦@slug⟧ token for compose pickers (same rules as commentReactionTokens). */
export function mentionReplacementFromSlug(slug: string): string {
  return mentionTokenFromProfileSlug(slug)
}
