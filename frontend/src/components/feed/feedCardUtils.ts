import type {
  CardCompany,
  CardMoodAfter,
  CardMoodBefore,
  FeedMovieCard,
  MovieCardComment,
  MovieCardCommentAuthor,
} from '../../api/profileTypes'
import { commentAuthorLabel, formatCommentTime, snippetPreview } from '../../lib/commentDisplay'
import { displayNameFromAuthorFields } from '../../lib/authorDisplayName'
import { formatRating, ratingDashOffset, ratingPalette } from '../../lib/ratingDisplay'

export { formatCommentTime, formatRating, ratingDashOffset, ratingPalette, snippetPreview }

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
    case 'feed_posts':
      return 'Пост'
    case 'own_cards':
      return 'Моя карточка'
    case 'global':
      return 'Публичное'
    default:
      return 'Лента'
  }
}

export function authorLabelFromAuthor(a: MovieCardCommentAuthor): string {
  return displayNameFromAuthorFields(a)
}

export function authorLabel(card: FeedMovieCard): string {
  return authorLabelFromAuthor(card.card_author)
}

export function commentAuthorDisplay(comment: MovieCardComment): string {
  return commentAuthorLabel(comment.author)
}
