import { Avatar, Button, Input, Section, Title } from '@telegram-apps/telegram-ui'
import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import {
  searchCatalog,
  searchSuggestions,
  type SearchFilmItem,
  type SearchSuggestionsResponse,
  type SearchUserItem,
} from '../api/searchApi'
import { ApiError, formatApiDetail } from '../api/client'
import { UserSuggestionChipsStrip } from '../components/search/UserSuggestionChipsStrip'
import { useAuthStatus } from '../auth/useAuthStatus'
import { profileInitials } from '../lib/profileDisplay'

function userListLabel(u: SearchUserItem): string {
  if (u.display_name?.trim()) {
    return u.display_name.trim()
  }
  if (u.username?.trim()) {
    return `@${u.username.trim()}`
  }
  return `@${u.profile_slug}`
}

function UserSuggestionRow({ user }: { user: SearchUserItem }) {
  const label = userListLabel(user)
  const initials = profileInitials({
    display_name: user.display_name,
    first_name: null,
    username: user.username,
  })
  return (
    <Link
      to={`/u/${encodeURIComponent(user.id)}`}
      className="flex min-h-[52px] items-center gap-3 rounded-xl px-2 py-2 no-underline text-(--tgui--text_color) transition-colors hover:bg-[color-mix(in_srgb,var(--tgui--hint_color)_12%,transparent)]"
    >
      <Avatar size={40} src={user.photo_url ?? undefined} acronym={initials} />
      <div className="min-w-0 flex-1">
        <div className="truncate font-medium">{label}</div>
        <div className="truncate text-sm text-(--tgui--hint_color)">@{user.profile_slug}</div>
      </div>
    </Link>
  )
}

function SearchSuggestionsChips({ data }: { data: SearchSuggestionsResponse }) {
  const hasAny =
    data.mutual_circle.length + data.popular_authors.length + data.random_with_cards.length > 0
  if (!hasAny) {
    return <p className="py-3 text-sm text-(--tgui--hint_color)">Пока мало данных для подсказок.</p>
  }
  return (
    <div className="flex flex-col">
      <UserSuggestionChipsStrip title="Рядом с вашим кругом" users={data.mutual_circle} />
      <UserSuggestionChipsStrip title="Активные в ленте" users={data.popular_authors} />
      <UserSuggestionChipsStrip title="Случайные с карточками" users={data.random_with_cards} />
    </div>
  )
}

function FilmResultRow({ film }: { film: SearchFilmItem }) {
  return (
    <Link
      to={`/films/${encodeURIComponent(String(film.id))}`}
      className="flex min-h-[56px] items-center gap-3 rounded-xl px-2 py-2 no-underline text-(--tgui--text_color) transition-colors hover:bg-[color-mix(in_srgb,var(--tgui--hint_color)_12%,transparent)]"
    >
      <div className="size-11 shrink-0 overflow-hidden rounded-lg bg-[color-mix(in_srgb,var(--tgui--hint_color)_18%,transparent)]">
        {film.poster_url ? (
          <img src={film.poster_url} alt="" className="size-full object-cover" loading="lazy" />
        ) : null}
      </div>
      <div className="min-w-0 flex-1">
        <div className="truncate font-medium">{film.title}</div>
        <div className="truncate text-sm text-(--tgui--hint_color)">
          {film.year != null ? `${film.year}` : 'Год не указан'}
        </div>
      </div>
    </Link>
  )
}

export function SearchPage() {
  const auth = useAuthStatus()
  const [query, setQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')

  useEffect(() => {
    const id = window.setTimeout(() => setDebouncedQuery(query.trim()), 320)
    return () => window.clearTimeout(id)
  }, [query])

  const canSearch = debouncedQuery.length >= 2

  const suggestionsQuery = useQuery({
    queryKey: ['search-suggestions'],
    queryFn: searchSuggestions,
    enabled: auth.kind === 'ready',
    staleTime: 5 * 60_000,
  })

  const searchQuery = useQuery({
    queryKey: ['search-catalog', debouncedQuery],
    queryFn: () => searchCatalog(debouncedQuery),
    enabled: auth.kind === 'ready' && canSearch,
    staleTime: 30_000,
  })

  const suggestionsError =
    suggestionsQuery.isError && suggestionsQuery.error instanceof ApiError
      ? formatApiDetail(suggestionsQuery.error.detail)
      : suggestionsQuery.isError
        ? 'Не удалось загрузить подсказки'
        : null

  const searchError =
    searchQuery.isError && searchQuery.error instanceof ApiError
      ? formatApiDetail(searchQuery.error.detail)
      : searchQuery.isError
        ? 'Ошибка поиска'
        : null

  const films = searchQuery.data?.films ?? []
  const users = searchQuery.data?.users ?? []

  const showFilmEmpty = canSearch && searchQuery.isSuccess && films.length === 0
  const showUserEmpty = canSearch && searchQuery.isSuccess && users.length === 0

  if (auth.kind === 'loading') {
    return (
      <main className="px-4 pt-4">
        <Title level="2">Поиск</Title>
        <p className="mt-3 text-(--tgui--hint_color)">Вход…</p>
      </main>
    )
  }

  if (auth.kind !== 'ready') {
    return (
      <main className="px-4 pt-4">
        <Title level="2">Поиск</Title>
        <p className="mt-3 text-(--tgui--hint_color)">Войдите в приложение, чтобы пользоваться поиском.</p>
      </main>
    )
  }

  return (
    <main className="px-4 pt-4 pb-2">
      <Title level="2" className="mb-1">
        Поиск
      </Title>
      <p className="mb-4 text-sm text-(--tgui--hint_color)">Тайтлы и люди в каталоге Filmony</p>

      <Section header="Запрос">
        <Input
          header="Строка поиска"
          placeholder="Минимум 2 символа"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </Section>

      {!canSearch && query.trim().length > 0 ? (
        <p className="mt-2 text-sm text-(--tgui--hint_color)">Введите ещё символы для поиска.</p>
      ) : null}

      {searchQuery.isFetching && canSearch ? (
        <p className="mt-3 text-sm text-(--tgui--hint_color)">Ищем…</p>
      ) : null}

      {searchError ? <p className="mt-2 text-sm text-(--tgui--destructive_text_color)">{searchError}</p> : null}

      {canSearch && searchQuery.isSuccess ? (
        <div className="mt-4 flex flex-col gap-6">
          <section>
            <h3 className="mb-2 text-[15px] font-semibold">Тайтлы</h3>
            {showFilmEmpty ? (
              <div className="rounded-xl bg-[color-mix(in_srgb,var(--tgui--hint_color)_10%,transparent)] px-3 py-4">
                <p className="mb-3 text-[15px] leading-snug">
                  Пока никто не добавлял этот тайтл. Можете первым — через ссылку с Кинопоиска.
                </p>
                <Link to="/cards/new" className="block w-full no-underline">
                  <Button mode="filled" stretched>
                    Добавить карточку
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="flex flex-col gap-1">
                {films.map((f) => (
                  <FilmResultRow key={f.id} film={f} />
                ))}
              </div>
            )}
          </section>

          <section>
            <h3 className="mb-2 text-[15px] font-semibold">Люди</h3>
            {showUserEmpty ? (
              <p className="rounded-xl bg-[color-mix(in_srgb,var(--tgui--hint_color)_10%,transparent)] px-3 py-4 text-[15px] leading-snug">
                Пользователей с таким именем не нашли.
              </p>
            ) : (
              <div className="flex flex-col gap-1">
                {users.map((u) => (
                  <UserSuggestionRow key={u.id} user={u} />
                ))}
              </div>
            )}
          </section>
        </div>
      ) : null}

      <div className="mt-4 -mx-4">
        {suggestionsQuery.isPending ? (
          <p className="px-4 pb-2 text-sm text-(--tgui--hint_color)">Загрузка подсказок…</p>
        ) : null}
        {suggestionsError ? (
          <p className="px-4 pb-2 text-sm text-(--tgui--destructive_text_color)">{suggestionsError}</p>
        ) : null}
        {suggestionsQuery.isSuccess && suggestionsQuery.data ? (
          <SearchSuggestionsChips data={suggestionsQuery.data} />
        ) : null}
      </div>
    </main>
  )
}
