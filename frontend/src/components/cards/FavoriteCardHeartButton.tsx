import { IconButton } from '@telegram-apps/telegram-ui'
import { Heart } from 'lucide-react'
import { useCallback, useState, type MouseEvent } from 'react'

import { updateMovieCard } from '../../api/cardApi'
import { ApiError, formatApiDetail } from '../../api/client'
import { safeHapticSuccess } from '../../lib/safeHaptic'

export type FavoriteCardHeartButtonProps = {
  cardId: number
  isFavorite: boolean
  onFavoriteChange: (next: boolean) => void
  onError?: (message: string) => void
  className?: string
}

export function FavoriteCardHeartButton({
  cardId,
  isFavorite,
  onFavoriteChange,
  onError,
  className = '',
}: FavoriteCardHeartButtonProps) {
  const [busy, setBusy] = useState(false)

  const onClick = useCallback(
    async (e: MouseEvent) => {
      e.preventDefault()
      e.stopPropagation()
      if (busy) return
      const next = !isFavorite
      onFavoriteChange(next)
      setBusy(true)
      try {
        await updateMovieCard(cardId, { is_favorite: next })
        safeHapticSuccess()
      } catch (err) {
        onFavoriteChange(!next)
        if (onError) {
          onError(err instanceof ApiError ? formatApiDetail(err.detail) : 'Не удалось обновить')
        }
      } finally {
        setBusy(false)
      }
    },
    [busy, cardId, isFavorite, onError, onFavoriteChange],
  )

  return (
    <IconButton
      type="button"
      size="s"
      mode="gray"
      disabled={busy}
      className={`border-0 !bg-black/40 shadow-md backdrop-blur-sm ${className}`}
      aria-label={isFavorite ? 'Убрать из любимых' : 'В любимые'}
      onClick={(e) => void onClick(e)}
    >
      <Heart
        className={`relative z-1 block size-[18px] ${
          isFavorite ? 'fill-red-500 text-red-500' : 'text-white/90'
        }`}
        strokeWidth={1.75}
        aria-hidden
      />
    </IconButton>
  )
}
