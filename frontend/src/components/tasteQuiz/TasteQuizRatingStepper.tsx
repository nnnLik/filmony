import { Button } from '@telegram-apps/telegram-ui'

import { normalizeRating, formatRating } from '../../lib/createCardBinding'

export type TasteQuizRatingStepperProps = {
  rating: number
  onRatingChange: (next: number) => void
  disabled?: boolean
}

export function TasteQuizRatingStepper({
  rating,
  onRatingChange,
  disabled = false,
}: TasteQuizRatingStepperProps) {
  const canDecrease = rating > 1
  const canIncrease = rating < 10

  return (
    <div className="flex flex-col items-center gap-3">
      <p
        className="text-4xl font-bold tabular-nums text-(--tgui--text_color)"
        aria-label={`Ваша оценка, ${formatRating(rating)} из 10`}
      >
        {formatRating(rating)}
      </p>
      <div className="flex items-center gap-3">
        <Button
          mode="gray"
          size="s"
          disabled={disabled || !canDecrease}
          aria-label="Уменьшить на 0.5"
          onClick={() => onRatingChange(normalizeRating(rating - 0.5))}
        >
          −
        </Button>
        <Button
          mode="gray"
          size="s"
          disabled={disabled || !canIncrease}
          aria-label="Увеличить на 0.5"
          onClick={() => onRatingChange(normalizeRating(rating + 0.5))}
        >
          +
        </Button>
      </div>
    </div>
  )
}
