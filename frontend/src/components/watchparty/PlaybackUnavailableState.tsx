import { PageErrorState } from '../ui/PageErrorState'

export const PLAYBACK_UNAVAILABLE_TITLE = 'Просмотр недоступен'

export const PLAYBACK_UNAVAILABLE_MESSAGE =
  'Этот фильм пока недоступен для просмотра в приложении'

type PlaybackUnavailableStateProps = {
  filmId: number
  className?: string
}

export function PlaybackUnavailableState({ filmId, className }: PlaybackUnavailableStateProps) {
  return (
    <PageErrorState
      title={PLAYBACK_UNAVAILABLE_TITLE}
      message={PLAYBACK_UNAVAILABLE_MESSAGE}
      backHref={`/films/${filmId}`}
      backLabel="К фильму"
      className={className ?? 'min-h-dvh bg-black'}
    />
  )
}
