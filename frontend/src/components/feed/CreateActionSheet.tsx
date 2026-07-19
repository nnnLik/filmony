import { Button, IconButton } from '@telegram-apps/telegram-ui'
import { X } from 'lucide-react'
import { createPortal } from 'react-dom'
import { useNavigate } from 'react-router-dom'

export type CreateActionSheetProps = {
  onClose: () => void
  onOpenCompose: () => void
}

export function CreateActionSheet({ onClose, onOpenCompose }: CreateActionSheetProps) {
  const navigate = useNavigate()

  const handleCard = () => {
    onClose()
    void navigate('/cards/new')
  }

  const handlePost = () => {
    onClose()
    onOpenCompose()
  }

  const handleWatchlist = () => {
    onClose()
    void navigate('/watchlist/new')
  }

  return createPortal(
    <div
      className="filmony-theme fixed inset-0 z-50 flex flex-col justify-end text-(--tgui--text_color) pointer-events-auto"
      aria-hidden={false}
    >
      <button
        type="button"
        className="absolute inset-0 bg-[color-mix(in_srgb,var(--filmony-ink,#06090d)_72%,transparent)] opacity-100 transition-opacity duration-200"
        tabIndex={0}
        aria-label="Закрыть"
        onClick={onClose}
      />
      <div
        className="relative z-10 isolate mx-auto flex w-full max-w-md flex-col rounded-t-[22px] border border-(--tgui--divider_color) bg-(--tgui--tertiary_bg_color) shadow-[0_-16px_48px_rgba(0,0,0,0.5),inset_0_1px_0_rgba(255,255,255,0.06)] motion-safe:animate-[filmony-detail-fade-in_0.2s_ease-out_both] ring-1 ring-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_14%,transparent)]"
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-action-sheet-title"
      >
        <div className="flex shrink-0 items-center justify-between gap-2 border-b border-[color-mix(in_srgb,var(--tgui--divider_color)_75%,transparent)] px-3 py-2.5">
          <h2
            id="create-action-sheet-title"
            className="min-w-0 flex-1 truncate text-[16px] font-semibold tracking-tight text-(--tgui--text_color)"
          >
            Создать
          </h2>
          <IconButton mode="gray" size="s" onClick={onClose} aria-label="Закрыть">
            <X className="block size-5" strokeWidth={2} />
          </IconButton>
        </div>

        <div className="flex flex-col gap-2 bg-(--tgui--bg_color) p-3 pb-[max(12px,calc(10px+env(safe-area-inset-bottom)))]">
          <Button mode="gray" stretched onClick={handleCard}>
            Карточка
          </Button>
          <p className="px-1 text-xs text-(--tgui--hint_color)">
            Оценить фильм, сериал или игру — с обложкой и полкой
          </p>
          <Button mode="gray" stretched onClick={handlePost}>
            Пост
          </Button>
          <p className="px-1 text-xs text-(--tgui--hint_color)">
            Короткая запись в ленту — мысль, ссылка, без карточки
          </p>
          <Button mode="gray" stretched onClick={handleWatchlist}>
            Позже
          </Button>
          <p className="px-1 text-xs text-(--tgui--hint_color)">
            Сохранить в watchlist без оценки
          </p>
        </div>
      </div>
    </div>,
    document.body,
  )
}
