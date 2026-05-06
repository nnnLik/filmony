import { Button, Cell, List, Section } from '@telegram-apps/telegram-ui'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { ApiError, formatApiDetail } from '../api/client'
import { getPublicProfileById, getPublicProfileBySlug, getUserCards } from '../api/profileApi'
import type { MovieCardPage, PublicProfile } from '../api/profileTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { ProfileHeader } from '../components/profile/ProfileHeader'

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

function isUuid(s: string) {
  return UUID_RE.test(s)
}

function decodeRouteIdentifier(raw: string | undefined): string {
  if (raw == null || raw === '') {
    return ''
  }
  try {
    return decodeURIComponent(raw)
  } catch {
    return raw
  }
}

export function PublicProfilePage() {
  const { identifier: rawIdentifier } = useParams<{ identifier?: string }>()
  const decodedId = useMemo(() => decodeRouteIdentifier(rawIdentifier), [rawIdentifier])
  const auth = useAuthStatus()
  const [profile, setProfile] = useState<PublicProfile | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [cards, setCards] = useState<MovieCardPage | null>(null)
  const [cardsError, setCardsError] = useState<string | null>(null)
  const [loadingMore, setLoadingMore] = useState(false)
  const prevRouteId = useRef<string | null>(null)

  useEffect(() => {
    if (auth.kind !== 'ready' || decodedId === '') {
      return
    }
    if (prevRouteId.current != null && prevRouteId.current !== decodedId) {
      setProfile(null)
      setCards(null)
    }
    prevRouteId.current = decodedId
    let alive = true
    void (async () => {
      await Promise.resolve()
      if (!alive) {
        return
      }
      setError(null)
      setCards(null)
      setCardsError(null)
      try {
        const p = isUuid(decodedId)
          ? await getPublicProfileById(decodedId)
          : await getPublicProfileBySlug(decodedId)
        if (!alive) {
          return
        }
        setProfile(p)
        const page = await getUserCards(p.id, { limit: 20 })
        if (!alive) {
          return
        }
        setCards(page)
      } catch (e) {
        if (!alive) {
          return
        }
        if (e instanceof ApiError) {
          setError(formatApiDetail(e.detail))
        } else {
          setError(e instanceof Error ? e.message : 'Ошибка загрузки')
        }
        setProfile(null)
        setCards(null)
      }
    })()
    return () => {
      alive = false
    }
  }, [auth.kind, decodedId])

  const loadMoreCards = useCallback(async () => {
    if (profile == null || cards?.next_cursor == null || cards.next_cursor === '') {
      return
    }
    setLoadingMore(true)
    setCardsError(null)
    try {
      const page = await getUserCards(profile.id, { cursor: cards.next_cursor, limit: 20 })
      setCards((prev) => {
        if (prev == null) {
          return page
        }
        return {
          items: [...prev.items, ...page.items],
          next_cursor: page.next_cursor,
        }
      })
    } catch (e) {
      if (e instanceof ApiError) {
        setCardsError(formatApiDetail(e.detail))
      } else {
        setCardsError(e instanceof Error ? e.message : 'Ошибка списка')
      }
    } finally {
      setLoadingMore(false)
    }
  }, [profile, cards])

  const canLoadMore = Boolean(cards?.next_cursor)

  if (auth.kind === 'loading') {
    return (
      <div className="px-4 py-16 text-center text-sm text-(--tgui--hint_color)">
        <p className="filmony-text-panel inline-block">Вход…</p>
      </div>
    )
  }

  if (auth.kind === 'error') {
    return (
      <div className="mx-auto max-w-md px-4 py-12">
        <p className="filmony-text-panel text-sm text-(--tgui--destructive_text_color)">{auth.message}</p>
        <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to="/">
          На главную
        </Link>
      </div>
    )
  }

  if (auth.kind === 'skipped') {
    return (
      <div className="mx-auto max-w-md px-4 py-12">
        <p className="filmony-text-panel text-sm text-(--tgui--hint_color)">
          Войдите через Telegram Mini App, чтобы открыть профиль.
        </p>
        <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to="/">
          На главную
        </Link>
      </div>
    )
  }

  if (decodedId === '') {
    return (
      <div className="px-4 py-10">
        <p className="filmony-text-panel text-sm text-(--tgui--hint_color)">Не указан пользователь.</p>
      </div>
    )
  }

  if (error != null) {
    return (
      <div className="mx-auto max-w-md px-4 py-12">
        <p className="filmony-text-panel text-sm text-(--tgui--destructive_text_color)">{error}</p>
        <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to="/profile">
          К профилю
        </Link>
      </div>
    )
  }

  if (profile == null) {
    return (
      <div className="px-4 py-16 text-center text-sm text-(--tgui--hint_color)">
        <p className="filmony-text-panel inline-block">Загрузка…</p>
      </div>
    )
  }

  return (
    <div className="min-h-dvh bg-(--tgui--bg_color) pb-6 text-(--tgui--text_color)">
      <header className="sticky top-0 z-20 flex items-center gap-2 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] px-2 py-2 backdrop-blur-md">
        <Link
          className="flex min-h-10 min-w-10 items-center justify-center rounded-lg text-lg text-(--tgui--link_color) no-underline"
          to="/profile"
          aria-label="Назад к профилю"
        >
          ←
        </Link>
        <span className="truncate text-sm font-medium text-(--tgui--hint_color)">Профиль</span>
      </header>

      <div className="mx-auto max-w-md px-4 pt-4">
        <ProfileHeader
          profile={profile}
          subtitle={`Карточек: ${profile.cards_count} · Друзей: ${profile.friends_count}`}
        />

        {profile.bio ? (
          <p className="filmony-text-panel mb-4 text-center text-sm leading-relaxed text-(--tgui--hint_color)">{profile.bio}</p>
        ) : null}

        <Section header="Фильмы">
          {cardsError != null ? (
            <p className="filmony-text-panel mx-4 my-2 text-sm text-(--tgui--destructive_text_color)">{cardsError}</p>
          ) : null}
          {cards != null && cards.items.length === 0 && !loadingMore ? (
            <p className="filmony-text-panel mx-4 my-4 text-center text-sm text-(--tgui--hint_color)">
              Пока нет карточек — позже здесь будет сетка постеров.
            </p>
          ) : null}
          {cards != null && cards.items.length > 0 ? (
            <List>
              {cards.items.map((card) => (
                <Cell
                  key={card.id}
                  subtitle={[
                    card.film_year != null ? String(card.film_year) : null,
                    `Оценка ${Number.isInteger(card.rating) ? card.rating : card.rating.toFixed(1)}`,
                  ]
                    .filter(Boolean)
                    .join(' · ')}
                >
                  {card.film_title}
                </Cell>
              ))}
            </List>
          ) : null}
          {canLoadMore ? (
            <div className="px-3 pb-3 pt-1">
              <Button disabled={loadingMore} stretched onClick={() => void loadMoreCards()}>
                {loadingMore ? 'Загрузка…' : 'Загрузить ещё'}
              </Button>
            </div>
          ) : null}
        </Section>
      </div>
    </div>
  )
}
