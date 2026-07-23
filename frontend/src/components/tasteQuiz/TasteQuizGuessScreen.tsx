import { Button } from '@telegram-apps/telegram-ui'

import type { TasteQuizSessionCard } from '../../api/tasteQuizTypes'
import { COMPANY_SHORT, MOOD_BEFORE_SHORT } from '../feed/feedCardUtils'
import { TasteQuizRatingStepper } from './TasteQuizRatingStepper'

export type TasteQuizGuessScreenProps = {
  card: TasteQuizSessionCard
  progressCurrent: number
  progressTotal: number
  rating: number
  onRatingChange: (next: number) => void
  submitBusy?: boolean
  onSubmit: () => void
  onAbandon: () => void
}

export function TasteQuizGuessScreen({
  card,
  progressCurrent,
  progressTotal,
  rating,
  onRatingChange,
  submitBusy = false,
  onSubmit,
  onAbandon,
}: TasteQuizGuessScreenProps) {
  return (
    <div className="mx-auto flex max-w-md flex-col px-4 py-4">
      <div
        className="mb-4 text-center text-sm text-(--tgui--hint_color)"
        role="progressbar"
        aria-valuenow={progressCurrent}
        aria-valuemax={progressTotal}
        aria-label={`Карточка ${progressCurrent} из ${progressTotal}`}
      >
        {progressCurrent} / {progressTotal}
      </div>

      <div className="overflow-hidden rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color)">
        <div className="aspect-[2/3] w-full bg-(--tgui--divider_color)">
          {card.poster_url ? (
            <img src={card.poster_url} alt="" className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-(--tgui--hint_color)">
              Нет постера
            </div>
          )}
        </div>
        <div className="px-4 py-4">
          <h2 className="text-lg font-semibold leading-snug text-(--tgui--text_color)">{card.title}</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            <span className="rounded-full bg-(--tgui--bg_color) px-2.5 py-1 text-xs text-(--tgui--text_color)">
              {COMPANY_SHORT[card.company] ?? card.company}
            </span>
            <span className="rounded-full bg-(--tgui--bg_color) px-2.5 py-1 text-xs text-(--tgui--text_color)">
              {MOOD_BEFORE_SHORT[card.mood_before] ?? card.mood_before}
            </span>
          </div>
        </div>
      </div>

      <div className="mt-8">
        <p className="mb-4 text-center text-sm text-(--tgui--hint_color)">Какую оценку поставил бы владелец?</p>
        <TasteQuizRatingStepper rating={rating} onRatingChange={onRatingChange} disabled={submitBusy} />
      </div>

      <div className="mt-8 space-y-2">
        <Button stretched disabled={submitBusy} onClick={onSubmit}>
          {submitBusy ? 'Отправка…' : 'Угадать'}
        </Button>
        <Button mode="gray" stretched disabled={submitBusy} onClick={onAbandon}>
          Выйти
        </Button>
      </div>
    </div>
  )
}
