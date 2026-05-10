import type {
  CardCompany,
  CardMoodAfter,
  CardMoodBefore,
  FeedMovieCard,
  MovieCardComment,
} from '../../api/profileTypes'

export const COMPANY_SHORT: Record<CardCompany, string> = {
  alone: 'Один',
  partner: 'Пара',
  friends: 'Друзья',
  family: 'Семья',
}

export const MOOD_BEFORE_SHORT: Record<CardMoodBefore, string> = {
  relax: 'Чилл',
  laugh: 'Юмор',
  sad: 'Грусть',
  thrill: 'Трилл',
}

export const MOOD_AFTER_SHORT: Record<CardMoodAfter, string> = {
  laughed: 'Ржал',
  cried: 'Тэш',
  enjoyed: 'Топ',
  tense: 'Выжат',
  wasted_time: 'Зря',
}

/** Короткий текст бейджа источника ленты (без длинных подписей в шапке карточки) */
export function feedCardSourceBadge(card: FeedMovieCard, viewerUserId: string | null): string {
  const isOwn =
    viewerUserId != null && viewerUserId !== '' && card.user_id === viewerUserId
  if (isOwn) {
    return 'Твоё'
  }
  switch (card.feed_source) {
    case 'subscriptions':
      return 'Подписка'
    case 'subscribers':
      return 'Подписчики'
    case 'personal_affinity':
      return 'По тегам'
    case 'discovery':
      return 'Новое'
    default:
      return 'Лента'
  }
}

export function ratingPalette(value: number): {
  ring: string
  glow: string
  text: string
  track: string
} {
  if (value <= 3) {
    return { ring: '#ef4444', glow: 'rgba(239,68,68,0.35)', text: '#fca5a5', track: 'rgba(239,68,68,0.15)' }
  }
  if (value <= 5) {
    return { ring: '#f59e0b', glow: 'rgba(245,158,11,0.32)', text: '#fcd34d', track: 'rgba(245,158,11,0.14)' }
  }
  if (value <= 7) {
    return { ring: '#84cc16', glow: 'rgba(132,204,22,0.3)', text: '#bef264', track: 'rgba(132,204,22,0.12)' }
  }
  return { ring: '#22c55e', glow: 'rgba(34,197,94,0.32)', text: '#86efac', track: 'rgba(34,197,94,0.12)' }
}

export function formatRating(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

export function authorLabel(card: FeedMovieCard): string {
  const a = card.card_author
  if (a.display_name && a.display_name.trim() !== '') {
    return a.display_name
  }
  if (a.username && a.username.trim() !== '') {
    return `@${a.username}`
  }
  const full = [a.first_name, a.last_name].filter(Boolean).join(' ').trim()
  return full === '' ? 'Автор' : full
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

export function commentAuthorDisplay(comment: MovieCardComment): string {
  const a = comment.author
  if (a.display_name && a.display_name.trim() !== '') {
    return a.display_name
  }
  if (a.username && a.username.trim() !== '') {
    return `@${a.username}`
  }
  const full = [a.first_name, a.last_name].filter(Boolean).join(' ').trim()
  return full === '' ? 'Пользователь' : full
}

export function snippetPreview(text: string): string {
  const compact = text.replace(/\s+/g, ' ').trim()
  if (compact.length <= 72) return compact
  return `${compact.slice(0, 69)}...`
}

/** Доля окружности (0–1) для шкалы 1–10 */
export function ratingDashOffset(value: number): number {
  const clamped = Math.min(10, Math.max(1, value))
  const p = (clamped - 1) / 9
  return 219.99 * (1 - p)
}
