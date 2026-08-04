import { Button } from '@telegram-apps/telegram-ui'
import { RefreshCw, WifiOff } from 'lucide-react'

import { formatOfflineCacheTimestamp } from '../../lib/formatOfflineCacheTimestamp'

type OfflineFeedBannerProps = {
  storedAt: number
  showRefresh: boolean
  onRefresh: () => void
  className?: string
}

export function OfflineFeedBanner({
  storedAt,
  showRefresh,
  onRefresh,
  className = '',
}: OfflineFeedBannerProps) {
  return (
    <div
      role="status"
      className={`sticky top-0 z-10 flex items-start gap-2.5 rounded-xl border border-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_45%,var(--tgui--divider_color))] bg-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_14%,var(--tgui--secondary_bg_color))] px-3 py-2.5 shadow-[0_4px_16px_-8px_rgba(0,0,0,0.35)] ${className}`.trim()}
    >
      <WifiOff
        className="mt-0.5 block size-4 shrink-0 text-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_88%,var(--tgui--text_color))]"
        strokeWidth={2.25}
        aria-hidden
      />
      <div className="min-w-0 flex-1">
        <p className="text-[12px] font-semibold leading-snug text-(--tgui--text_color)">
          Показана сохранённая лента
        </p>
        <p className="mt-0.5 text-[11px] leading-snug text-(--tgui--hint_color)">
          Данные от {formatOfflineCacheTimestamp(storedAt)}.
          {showRefresh ? ' Проверьте сеть и обновите ленту.' : ' Подгружаем актуальные записи…'}
        </p>
      </div>
      {showRefresh ? (
        <Button
          type="button"
          mode="bezeled"
          size="s"
          className="shrink-0"
          onClick={onRefresh}
        >
          <RefreshCw className="mr-1.5 block size-3.5" strokeWidth={2.25} aria-hidden />
          Обновить
        </Button>
      ) : null}
    </div>
  )
}
