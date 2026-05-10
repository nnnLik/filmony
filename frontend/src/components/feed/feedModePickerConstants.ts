import type { FeedListMode } from '../../api/profileTypes'

export const FEED_MODE_ENTRIES: Array<{
  value: FeedListMode
  title: string
  /** Короткая подпись на вкладке (узкий экран). */
  segmentLabel: string
  hint: string
}> = [
  {
    value: 'default',
    title: 'Для вас',
    segmentLabel: 'Для вас',
    hint: 'Подписки, подписчики, похожее по тегам и новые авторы',
  },
  {
    value: 'subscriptions_only',
    title: 'Из подписок',
    segmentLabel: 'Подписки',
    hint: 'Люди, на которых вы подписаны, и ваши карточки',
  },
  {
    value: 'subscribers_only',
    title: 'От подписчиков',
    segmentLabel: 'Подписчики',
    hint: 'Те, кто подписан на вас, и ваши карточки',
  },
]

export function feedModeTitle(mode: FeedListMode): string {
  return FEED_MODE_ENTRIES.find((e) => e.value === mode)?.title ?? 'Для вас'
}

export function feedModeHint(mode: FeedListMode): string {
  return FEED_MODE_ENTRIES.find((e) => e.value === mode)?.hint ?? ''
}
