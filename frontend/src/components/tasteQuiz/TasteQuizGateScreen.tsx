import { Button } from '@telegram-apps/telegram-ui'
import { Link } from 'react-router-dom'

export type TasteQuizGateScreenProps = {
  ownerName?: string | null
  ownerRatedCount: number
  gateMinRatedCards: number
  isOwnerViewer?: boolean
  onBack?: () => void
}

export function TasteQuizGateScreen({
  ownerName,
  ownerRatedCount,
  gateMinRatedCards,
  isOwnerViewer = false,
  onBack,
}: TasteQuizGateScreenProps) {
  return (
    <div className="mx-auto flex min-h-[60dvh] max-w-md flex-col items-center justify-center px-4 py-10 text-center">
      <div
        className="mb-6 flex size-20 items-center justify-center rounded-3xl bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_14%,var(--tgui--secondary_bg_color))] text-3xl"
        aria-hidden
      >
        🎯
      </div>
      <h2 className="text-lg font-semibold text-(--tgui--text_color)">Нужно минимум {gateMinRatedCards} оценённых карточек</h2>
      <p className="filmony-text-panel mt-3 text-sm leading-relaxed text-(--tgui--hint_color)">
        {isOwnerViewer
          ? `У вас сейчас ${ownerRatedCount}. Добавьте ещё оценённые карточки, чтобы друзья могли угадывать ваш вкус.`
          : `У ${ownerName ?? 'этого пользователя'} пока ${ownerRatedCount} оценённых карточек — для квиза нужно хотя бы ${gateMinRatedCards}.`}
      </p>
      <div className="mt-8 flex w-full max-w-xs flex-col gap-2">
        {isOwnerViewer ? (
          <Link to="/cards/new" className="no-underline">
            <Button stretched>Добавить карточку</Button>
          </Link>
        ) : null}
        {onBack != null ? (
          <Button mode="gray" stretched onClick={onBack}>
            Назад
          </Button>
        ) : (
          <Link to="/" className="no-underline">
            <Button mode="gray" stretched>
              На главную
            </Button>
          </Link>
        )}
      </div>
    </div>
  )
}
