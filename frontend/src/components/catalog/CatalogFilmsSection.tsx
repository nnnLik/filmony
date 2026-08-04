import { Button, Section } from '@telegram-apps/telegram-ui'

import { CatalogRatedFilmRow, type CatalogRatedFilm } from './CatalogRatedFilmRow'

type CatalogFilmsSectionProps = {
  films: CatalogRatedFilm[]
  isPending: boolean
  emptyMessage: string
  hasNextPage: boolean
  isFetchingNextPage: boolean
  onLoadMore: () => void
}

export function CatalogFilmsSection({
  films,
  isPending,
  emptyMessage,
  hasNextPage,
  isFetchingNextPage,
  onLoadMore,
}: CatalogFilmsSectionProps) {
  return (
    <Section header="Фильмы в Filmony">
      {films.length === 0 && !isPending ? (
        <p className="px-3 py-4 text-sm text-(--tgui--hint_color)">{emptyMessage}</p>
      ) : (
        <ul className="divide-y divide-(--tgui--divider_color)">
          {films.map((film) => (
            <CatalogRatedFilmRow key={film.film_id} film={film} />
          ))}
        </ul>
      )}

      {hasNextPage ? (
        <div className="px-3 py-3">
          <Button
            stretched
            mode="bezeled"
            disabled={isFetchingNextPage}
            onClick={() => {
              onLoadMore()
            }}
          >
            {isFetchingNextPage ? 'Подгружаем…' : 'Подгрузить ещё'}
          </Button>
        </div>
      ) : null}
    </Section>
  )
}
