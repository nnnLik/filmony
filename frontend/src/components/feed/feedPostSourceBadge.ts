import type { FeedPostInFeed } from '../../api/feedInFeedTypes'

/** Бейдж источника для текстового поста в ленте */
export function feedPostSourceBadge(post: FeedPostInFeed, viewerUserId: string | null): string {
  if (post.referenced_card?.is_planned) {
    return 'Запланировано'
  }
  const isOwn =
    viewerUserId != null && viewerUserId !== '' && post.user_id === viewerUserId
  if (isOwn) {
    return 'Твой пост'
  }
  switch (post.feed_source) {
    case 'subscriptions':
      return 'Подписка'
    case 'subscribers':
      return 'Подписчики'
    case 'personal_affinity':
      return 'По тегам'
    case 'discovery':
      return 'Новое'
    case 'feed_posts':
    default:
      return 'Пост'
  }
}
