import { Avatar, Button, Title } from '@telegram-apps/telegram-ui'
import { useQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { useEffect, useState, type ReactNode } from 'react'
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
import { resolveApiMediaUrl } from '../lib/resolveApiMediaUrl'
import { profileInitials } from '../lib/profileDisplay'

function posterSrc(url: string | null): string | undefined {
  if (!url?.trim()) return undefined
  const t = url.trim()
  if (t.startsWith('http://') || t.startsWith('https://')) return t
  return resolveApiMediaUrl(t)
}

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
      className="flex min-h-[52px] items-center gap-3 rounded-xl px-2.5 py-2 no-underline text-(--tgui--text_color) transition-colors hover:bg-[color-mix(in_srgb,var(--tgui--hint_color)_10%,transparent)] active:bg-[color-mix(in_srgb,var(--tgui--hint_color)_14%,transparent)]"
    >
      <Avatar size={40} src={user.photo_url ?? undefined} acronym={initials} />
      <div className="min-w-0 flex-1">
        <div className="truncate font-medium">{label}</div>
        <div className="truncate text-sm text-(--tgui--hint_color)">@{user.profile_slug}</div>
      </div>
    </Link>
  )
}

function SearchSuggestionsBlocks({ data }: { data: SearchSuggestionsResponse }) {
  const hasAny =
    data.mutual_circle.length + data.popular_authors.length + data.random_with_cards.length > 0
  if (!hasAny) {
    return (
      <div className="rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_92%,transparent)] px-4 py-5 text-center">
        <p className="text-[14px] leading-relaxed text-(--tgui--hint_color)">
          Пока мало данных для подсказок — добавьте подписки и карточки, сообщество подрастёт.
        </p>
      </div>
    )
  }
  return (
    <div className="flex flex-col gap-3">
      <UserSuggestionChipsStrip
        title="Рядом с вашим кругом"
        hint="Те, с кем похожие подписки — возможные новые знакомства"
        users={data.mutual_circle}
      />
      <UserSuggestionChipsStrip
        title="Активные в ленте"
        hint="За последнюю неделю по новым карточкам"
        users={data.popular_authors}
      />
      <UserSuggestionChipsStrip
        title="Случайные с карточками"
        hint="Живой каталог — загляните в профиль"
        users={data.random_with_cards}
      />
    </div>
  )
}

function FilmResultRow({ film }: { film: SearchFilmItem }) {
  const src = posterSrc(film.poster_url)
  return (
    <Link
      to={`/films/${encodeURIComponent(String(film.id))}`}
      className="flex min-h-[56px] items-center gap-3 rounded-xl px-2.5 py-2 no-underline text-(--tgui--text_color) transition-colors hover:bg-[color-mix(in_srgb,var(--tgui--hint_color)_10%,transparent)] active:bg-[color-mix(in_srgb,var(--tgui--hint_color)_14%,transparent)]"
    >
      <div className="size-11 shrink-0 overflow-hidden rounded-xl bg-[color-mix(in_srgb,var(--tgui--hint_color)_14%,transparent)] ring-1 ring-(--tgui--divider_color)">
        {src ? (
          <img src={src} alt="" className="size-full object-cover" loading="lazy" />
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

function ResultsSection({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle?: string
  children: ReactNode
}) {
  return (
    <section className="rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_92%,transparent)] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,.03)]">
      <div className="mb-2 px-0.5">
        <h3 className="text-[15px] font-semibold tracking-tight text-(--tgui--text_color)">{title}</h3>
        {subtitle ? <p className="mt-0.5 text-[12px] text-(--tgui--hint_color)">{subtitle}</p> : null}
      </div>
      {children}
    </section>
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
      <div className="min-h-full">
        <header className="border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_92%,transparent)] px-4 py-3 backdrop-blur-md">
          <Title level="2">Поиск</Title>
        </header>
        <main className="px-4 pt-4">
          <p className="text-sm text-(--tgui--hint_color)">Вход…</p>
        </main>
      </div>
    )
  }

  if (auth.kind !== 'ready') {
    return (
      <div className="min-h-full">
        <header className="border-b border-(--tgui--divider_color) px-4 py-3">
          <Title level="2">Поиск</Title>
        </header>
        <main className="px-4 pt-4">
          <p className="text-sm text-(--tgui--hint_color)">Войдите в приложение, чтобы пользоваться поиском.</p>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-20 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] backdrop-blur-md">
        <div className="px-4 py-3">
          <h1 className="bg-linear-to-r from-(--filmony-mint,#5eead4) via-(--filmony-text,#e8f0f7) to-(--filmony-amber,#e8b86d) bg-clip-text text-lg font-semibold tracking-tight text-transparent">
            Поиск
          </h1>
          <p className="mt-1 text-[13px] leading-snug text-(--tgui--hint_color)">
            Кого посмотреть и что найти в каталоге Filmony
          </p>
        </div>
      </header>

      <main className="max-w-full overflow-x-hidden px-4 pb-10 pt-4">
        <div className="flex flex-col gap-5">
          {/* Подсказки сверху — как в продуктовой спецификации */}
          {suggestionsQuery.isPending ? (
            <p className="text-center text-sm text-(--tgui--hint_color)">Загружаем идеи для вас…</p>
          ) : null}
          {suggestionsError ? (
            <div className="rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_92%,transparent)] px-4 py-4">
              <p className="text-[14px] text-(--tgui--destructive_text_color)">{suggestionsError}</p>
            </div>
          ) : null}
          {suggestionsQuery.isSuccess && suggestionsQuery.data ? (
            <SearchSuggestionsBlocks data={suggestionsQuery.data} />
          ) : null}

          {/* Строка поиска — одна «карточка», без вложенных Section */}
          <div>
            <label htmlFor="search-catalog-input" className="sr-only">
              Поиск по каталогу
            </label>
            <div className="flex items-center gap-2.5 rounded-2xl border border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_24%,var(--tgui--divider_color))] bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_88%,transparent)] px-3.5 py-2.5 shadow-[inset_0_1px_0_rgba(255,255,255,.05)] transition-[border-color,box-shadow] duration-200 focus-within:border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_45%,transparent)] focus-within:shadow-[0_0_0_3px_color-mix(in_srgb,var(--filmony-mint,#5eead4)_12%,transparent)]">
              <Search
                className="pointer-events-none size-5 shrink-0 text-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_75%,var(--tgui--hint_color))]"
                strokeWidth={2}
                aria-hidden
              />
              <input
                id="search-catalog-input"
                type="search"
                name="q"
                enterKeyHint="search"
                autoComplete="off"
                autoCorrect="off"
                spellCheck={false}
                placeholder="Найти тайтл или человека…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="min-w-0 flex-1 border-0 bg-transparent py-0.5 text-[16px] text-(--tgui--text_color) outline-none placeholder:text-(--tgui--hint_color)"
              />
            </div>
            {!canSearch && query.trim().length > 0 ? (
              <p className="mt-2 px-0.5 text-[12px] text-(--tgui--hint_color)">Ещё один символ — и покажем результаты.</p>
            ) : null}
            {searchQuery.isFetching && canSearch ? (
              <p className="mt-2 px-0.5 text-[12px] text-(--tgui--hint_color)">Ищем в каталоге…</p>
            ) : null}
            {searchError ? (
              <p className="mt-2 px-0.5 text-[13px] text-(--tgui--destructive_text_color)">{searchError}</p>
            ) : null}
          </div>

          {canSearch && searchQuery.isSuccess ? (
            <div className="flex flex-col gap-4">
              <ResultsSection title="Тайтлы" subtitle="Уже в каталоге Filmony">
                {showFilmEmpty ? (
                  <div className="rounded-xl bg-[color-mix(in_srgb,var(--tgui--hint_color)_08%,transparent)] px-3 py-4">
                    <p className="mb-3 text-[14px] leading-relaxed text-(--tgui--text_color)">
                      Пока никто не добавлял этот тайтл. Можете первым — через ссылку с Кинопоиска.
                    </p>
                    <Link to="/cards/new" className="block w-full no-underline">
                      <Button mode="filled" stretched>
                        Добавить карточку
                      </Button>
                    </Link>
                  </div>
                ) : (
                  <div className="flex flex-col gap-0.5">
                    {films.map((f) => (
                      <FilmResultRow key={f.id} film={f} />
                    ))}
                  </div>
                )}
              </ResultsSection>

              <ResultsSection title="Люди" subtitle="По имени, нику или адресу профиля">
                {showUserEmpty ? (
                  <p className="rounded-xl bg-[color-mix(in_srgb,var(--tgui--hint_color)_08%,transparent)] px-3 py-4 text-[14px] leading-relaxed text-(--tgui--text_color)">
                    Пользователей с таким именем не нашли.
                  </p>
                ) : (
                  <div className="flex flex-col gap-0.5">
                    {users.map((u) => (
                      <UserSuggestionRow key={u.id} user={u} />
                    ))}
                  </div>
                )}
              </ResultsSection>
            </div>
          ) : null}
        </div>
      </main>
    </div>
  )
}
