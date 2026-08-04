import type { ProfileMoviesSegment } from '../../lib/profileMoviesSegment'

type ProfileMoviesSegmentToggleProps = {
  value: ProfileMoviesSegment
  onChange: (segment: ProfileMoviesSegment) => void
  className?: string
}

export function ProfileMoviesSegmentToggle({
  value,
  onChange,
  className,
}: ProfileMoviesSegmentToggleProps) {
  return (
    <div className={`flex gap-1 rounded-full bg-(--tgui--secondary_bg_color) p-1 ${className ?? ''}`}>
      <button
        type="button"
        className={`flex flex-1 items-center justify-center gap-2 rounded-full py-2.5 text-sm font-medium transition-all ${
          value === 'rated'
            ? 'bg-(--tgui--bg_color) text-(--tgui--text_color) shadow-sm'
            : 'text-(--tgui--hint_color)'
        }`}
        onClick={() => onChange('rated')}
      >
        Оценённые
      </button>
      <button
        type="button"
        className={`flex flex-1 items-center justify-center gap-2 rounded-full py-2.5 text-sm font-medium transition-all ${
          value === 'watchlist'
            ? 'bg-(--tgui--bg_color) text-(--tgui--text_color) shadow-sm'
            : 'text-(--tgui--hint_color)'
        }`}
        onClick={() => onChange('watchlist')}
      >
        Позже
      </button>
    </div>
  )
}
