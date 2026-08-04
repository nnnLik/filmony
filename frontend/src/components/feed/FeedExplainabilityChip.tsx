import type { FeedPostInFeed } from '../../api/feedInFeedTypes'
import type { FeedMovieCard } from '../../api/profileTypes'
import { feedCardSourceBadge } from './feedCardUtils'
import { feedPostSourceBadge } from './feedPostSourceBadge'

type FeedExplainabilityChipProps =
  | {
      variant: 'card'
      card: FeedMovieCard
      viewerUserId?: string | null
    }
  | {
      variant: 'post'
      post: FeedPostInFeed
      viewerUserId?: string | null
    }

function isOwnAuthor(authorUserId: string, viewerUserId: string | null | undefined): boolean {
  return viewerUserId != null && viewerUserId !== '' && authorUserId === viewerUserId
}

function feedSourceTitle(
  feedSource: FeedMovieCard['feed_source'],
  isOwn: boolean,
  variant: 'card' | 'post',
): string {
  if (isOwn) {
    return variant === 'card' ? 'Твоя карточка' : 'Твой пост в ленте'
  }
  switch (feedSource) {
    case 'subscriptions':
      return 'Из подписок'
    case 'subscribers':
      return 'Из подписчиков'
    case 'personal_affinity':
      return 'Похоже на ваши теги'
    case 'discovery':
      return 'Рекомендации'
    case 'feed_posts':
      return 'Текстовый пост в ленте'
    case 'own_cards':
      return 'Карточка автора в ленте'
    case 'global':
      return 'Публичная лента'
    default:
      return 'Источник в ленте'
  }
}

export function FeedExplainabilityChip(props: FeedExplainabilityChipProps) {
  const viewerUserId = props.viewerUserId ?? null
  const isCard = props.variant === 'card'
  const authorUserId = isCard ? props.card.user_id : props.post.user_id
  const feedSource = isCard ? props.card.feed_source : props.post.feed_source
  const isOwn = isOwnAuthor(authorUserId, viewerUserId)
  const label = isCard
    ? feedCardSourceBadge(props.card, viewerUserId)
    : feedPostSourceBadge(props.post, viewerUserId)
  const title = feedSourceTitle(feedSource, isOwn, props.variant)

  const cardStyles =
    'border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_38%,transparent)] bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_10%,transparent)]'
  const postStyles =
    'border-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_42%,transparent)] bg-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_12%,transparent)]'

  return (
    <span
      className={`shrink-0 rounded-md border px-1.5 py-0.5 text-[10px] font-semibold tracking-wide text-(--tgui--text_color) ${
        isCard ? cardStyles : postStyles
      }`}
      title={title}
    >
      {label}
    </span>
  )
}
