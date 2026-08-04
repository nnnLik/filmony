import type { MovieCardCommentAuthor } from '../api/profileTypes'

/** Human-readable label for a comment author (detail pages, thread UI). */
export function commentAuthorLabel(author: MovieCardCommentAuthor): string {
  if (author.display_name != null && author.display_name.trim() !== '') {
    return author.display_name
  }
  if (author.username != null && author.username.trim() !== '') {
    return `@${author.username}`
  }
  const full = [author.first_name, author.last_name].filter(Boolean).join(' ').trim()
  return full === '' ? 'Пользователь' : full
}

export function snippetPreview(text: string): string {
  const compact = text.replace(/\s+/g, ' ').trim()
  if (compact.length <= 72) return compact
  return `${compact.slice(0, 69)}...`
}

export function formatCommentTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return ''
  }
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
