import { Button } from '@telegram-apps/telegram-ui'

import type { TasteQuizSessionCard, TasteQuizVerdictKey } from '../../api/tasteQuizTypes'
import { formatRating } from '../../lib/createCardBinding'
import { SpoilerRevealBlock } from '../comments/SpoilerRevealBlock'
import { MOOD_AFTER_SHORT } from '../feed/feedCardUtils'

const VERDICT_COPY: Record<TasteQuizVerdictKey, { headline: string; points: string }> = {
  exact: { headline: 'В точку! Ты читаешь мысли.', points: '+1' },
  close: { headline: 'Почти! Промах на полшага.', points: '+0.5' },
  miss: { headline: 'Мимо. Вкусы разошлись.', points: '0' },
}

function verdictCopy(key: string | null | undefined) {
  if (key === 'exact' || key === 'close' || key === 'miss') {
    return VERDICT_COPY[key]
  }
  return { headline: 'Результат', points: '—' }
}

export type TasteQuizRevealScreenProps = {
  card: TasteQuizSessionCard
  onContinue: () => void
}

export function TasteQuizRevealScreen({ card, onContinue }: TasteQuizRevealScreenProps) {
  const copy = verdictCopy(card.verdict_key)
  const ownerRating = card.owner_rating ?? 0
  const guessRating = card.guess_rating ?? 0
  const delta = Math.abs(ownerRating - guessRating)

  return (
    <div className="mx-auto flex max-w-md flex-col px-4 py-6">
      <div className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-4 py-6 text-center">
        <p className="text-3xl font-bold tabular-nums text-(--filmony-mint,#5eead4)">{copy.points}</p>
        <h2 className="mt-2 text-lg font-semibold text-(--tgui--text_color)">{copy.headline}</h2>
        <div className="mt-4 flex items-center justify-center gap-6 text-sm">
          <div>
            <p className="text-xs text-(--tgui--hint_color)">Вы</p>
            <p className="text-xl font-semibold tabular-nums text-(--tgui--text_color)">
              {formatRating(guessRating)}
            </p>
          </div>
          <div className="text-(--tgui--hint_color)">Δ {formatRating(delta)}</div>
          <div>
            <p className="text-xs text-(--tgui--hint_color)">Владелец</p>
            <p className="text-xl font-semibold tabular-nums text-(--tgui--link_color)">
              {formatRating(ownerRating)}
            </p>
          </div>
        </div>
      </div>

      {card.mood_after != null ? (
        <div className="mt-4 flex justify-center">
          <span className="rounded-full bg-(--tgui--secondary_bg_color) px-3 py-1.5 text-sm text-(--tgui--text_color)">
            После: {MOOD_AFTER_SHORT[card.mood_after] ?? card.mood_after}
          </span>
        </div>
      ) : null}

      {card.watch_note != null && card.watch_note.trim() !== '' ? (
        <div className="mt-4 rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-4 py-3">
          <p className="text-xs text-(--tgui--hint_color)">Заметка</p>
          <p className="mt-1 text-sm leading-relaxed text-(--tgui--text_color)">
            <SpoilerRevealBlock>{card.watch_note}</SpoilerRevealBlock>
          </p>
        </div>
      ) : null}

      <Button className="mt-8" stretched onClick={onContinue}>
        Дальше
      </Button>
    </div>
  )
}
