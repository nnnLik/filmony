import { Button } from '@telegram-apps/telegram-ui'
import { Link } from 'react-router-dom'

import type { TasteQuizPairProgress, TasteQuizSession } from '../../api/tasteQuizTypes'
import { formatRating } from '../../lib/createCardBinding'
import { tasteQuizAccuracyColor } from '../../lib/tasteQuizAccuracyColor'

export type TasteQuizSummaryScreenProps = {
  session: TasteQuizSession
  pairProgress: TasteQuizPairProgress | null
  ownerName: string
  ownerUserId: string
  onPlayAgain?: () => void
  playAgainDisabled?: boolean
}

export function TasteQuizSummaryScreen({
  session,
  pairProgress,
  ownerName,
  ownerUserId,
  onPlayAgain,
  playAgainDisabled = false,
}: TasteQuizSummaryScreenProps) {
  const answeredCards = session.cards.filter((c) => c.answered_at != null)
  const maxPoints = answeredCards.length
  const sessionAccuracy =
    maxPoints > 0 ? Math.round((session.round_points / maxPoints) * 100) : 0
  const edgeColor =
    pairProgress != null ? tasteQuizAccuracyColor(pairProgress.accuracy_pct) : undefined

  return (
    <div className="mx-auto flex max-w-md flex-col px-4 py-6">
      <div className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-4 py-6 text-center">
        <p className="text-xs uppercase tracking-wide text-(--tgui--hint_color)">Итог сессии</p>
        <p className="mt-2 text-4xl font-bold tabular-nums text-(--filmony-mint,#5eead4)">
          {formatRating(session.round_points)} / {maxPoints}
        </p>
        <p className="mt-1 text-sm text-(--tgui--hint_color)">Точность раунда: {sessionAccuracy}%</p>
      </div>

      {pairProgress != null && pairProgress.attempts > 0 ? (
        <p className="filmony-text-panel mt-6 text-center text-sm leading-relaxed text-(--tgui--text_color)">
          Теперь ты знаешь вкус {ownerName} на{' '}
          <span className="font-semibold tabular-nums" style={{ color: edgeColor }}>
            {pairProgress.accuracy_pct}%
          </span>
        </p>
      ) : null}

      {answeredCards.length > 0 ? (
        <ul className="mt-6 space-y-2">
          {answeredCards.map((card) => (
            <li
              key={card.session_card_id}
              className="flex items-center justify-between gap-2 rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-3 py-2 text-sm"
            >
              <span className="min-w-0 truncate text-(--tgui--text_color)">{card.title}</span>
              <span className="shrink-0 tabular-nums text-(--tgui--hint_color)">
                {formatRating(card.guess_rating ?? 0)} → {formatRating(card.owner_rating ?? 0)}{' '}
                <span className="text-(--tgui--link_color)">+{formatRating(card.round_points ?? 0)}</span>
              </span>
            </li>
          ))}
        </ul>
      ) : null}

      <div className="mt-8 space-y-2">
        <Link to={`/u/${encodeURIComponent(ownerUserId)}`} className="no-underline">
          <Button stretched mode="gray">
            На профиль
          </Button>
        </Link>
        {onPlayAgain != null ? (
          <Button stretched disabled={playAgainDisabled} onClick={onPlayAgain}>
            Ещё раз
          </Button>
        ) : null}
      </div>
    </div>
  )
}
