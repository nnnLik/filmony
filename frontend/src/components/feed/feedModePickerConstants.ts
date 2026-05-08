import type { FeedListMode } from '../../api/profileTypes'

export const FEED_MODE_ENTRIES: Array<{
  value: FeedListMode
  title: string
  hint: string
}> = [
  {
    value: 'default',
    title: 'Для вас',
    hint: 'Подписки, подписчики, похожее по тегам и новые авторы',
  },
  {
    value: 'subscriptions_only',
    title: 'Из подписок',
    hint: 'Люди, на которых вы подписаны, и ваши карточки',
  },
  {
    value: 'subscribers_only',
    title: 'От подписчиков',
    hint: 'Те, кто подписан на вас, и ваши карточки',
  },
]

export function feedModeTitle(mode: FeedListMode): string {
  return FEED_MODE_ENTRIES.find((e) => e.value === mode)?.title ?? 'Для вас'
}
