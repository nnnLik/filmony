import { Button, Section, Title } from '@telegram-apps/telegram-ui'
import { useInfiniteQuery } from '@tanstack/react-query'
import { ChevronLeft } from 'lucide-react'
import { Link, useNavigate } from 'react-router'

import { getDirectorsCatalogPage } from '../api/directorsApi'
import { ApiError, formatApiDetail } from '../api/client'
import { useAuthStatus } from '../auth/useAuthStatus'
import { directorChipStyles } from '../lib/directorColor'

function directorsCatalogQueryKey() {
  return ['directorsCatalog'] as const
}

export function DirectorsIndexPage() {
  const auth = useAuthStatus()
  const navigate = useNavigate()

  const catalogQuery = useInfiniteQuery({
    queryKey: directorsCatalogQueryKey(),
    queryFn: ({ pageParam }) =>
      getDirectorsCatalogPage({
        cursor: pageParam ?? null,
        limit: 50,
      }),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next_cursor,
    enabled: auth.kind === 'ready',
    staleTime: 60_000,
  })

  const items = catalogQuery.data?.pages.flatMap((page) => page.items) ?? []

  const listErr =
    catalogQuery.error instanceof ApiError
      ? formatApiDetail(catalogQuery.error.detail)
      : catalogQuery.error != null
        ? 'Не удалось загрузить режиссёров'
        : null

  if (auth.kind === 'loading' || auth.kind === 'skipped') {
    return (
      <div className="min-h-dvh bg-(--tgui--bg_color) px-4 py-16 text-center text-sm text-(--tgui--hint_color)">
        Вход…
      </div>
    )
  }

  return (
    <div className="min-h-dvh bg-(--tgui--bg_color) pb-8 text-(--tgui--text_color)">
      <header className="sticky top-0 z-20 flex items-center gap-2 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] px-2 py-2 backdrop-blur-md">
        <button
          type="button"
          className="flex size-9 items-center justify-center rounded-full text-(--tgui--text_color) outline-none active:opacity-80"
          aria-label="Назад"
          onClick={() => void navigate(-1)}
        >
          <ChevronLeft className="block size-5" strokeWidth={1.75} aria-hidden />
        </button>
        <span className="truncate text-sm font-medium">Режиссёры</span>
      </header>

      <main className="mx-auto max-w-md px-4 pt-4">
        <Title level="2" weight="2">
          Режиссёры в Filmony
        </Title>
        <p className="mt-1 text-sm text-(--tgui--hint_color)">
          Фильмы с оценками сообщества, сгруппированные по режиссёру.
        </p>

        {catalogQuery.isPending ? (
          <p className="filmony-text-panel py-12 text-center text-sm text-(--tgui--hint_color)">Загрузка…</p>
        ) : null}

        {listErr != null ? (
          <p className="mt-4 text-sm text-(--tgui--destructive_text_color)">{listErr}</p>
        ) : null}

        {items.length === 0 && !catalogQuery.isPending && listErr == null ? (
          <p className="mt-6 text-sm text-(--tgui--hint_color)">Пока нет режиссёров в каталоге</p>
        ) : (
          <Section header="Список">
            <ul className="divide-y divide-(--tgui--divider_color)">
              {items.map((row) => {
                const accent = directorChipStyles(row.kinopoisk_id)
                return (
                  <li key={row.kinopoisk_id}>
                    <Link
                      to={`/directors/${row.kinopoisk_id}`}
                      className={`flex items-center justify-between gap-3 px-3 py-3 no-underline outline-none transition-[background-color] active:bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_88%,transparent)] focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-(--tgui--link_color) ${accent.backgroundClass}`}
                    >
                      <span className="min-w-0 truncate text-sm font-medium text-(--tgui--text_color)">
                        {row.name}
                      </span>
                      <span className="shrink-0 text-xs tabular-nums text-(--tgui--hint_color)">
                        {row.films_count}{' '}
                        {row.films_count === 1 ? 'фильм' : row.films_count < 5 ? 'фильма' : 'фильмов'}
                      </span>
                    </Link>
                  </li>
                )
              })}
            </ul>
          </Section>
        )}

        {catalogQuery.hasNextPage ? (
          <div className="mt-4">
            <Button
              stretched
              mode="bezeled"
              disabled={catalogQuery.isFetchingNextPage}
              onClick={() => void catalogQuery.fetchNextPage()}
            >
              {catalogQuery.isFetchingNextPage ? 'Подгружаем…' : 'Подгрузить ещё'}
            </Button>
          </div>
        ) : null}
      </main>
    </div>
  )
}
