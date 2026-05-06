import { Avatar, Button, Section, Title } from '@telegram-apps/telegram-ui'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { ApiError, formatApiDetail } from '../api/client'
import { getMyProfile, getUserCards } from '../api/profileApi'
import type { MovieCardPage, MyProfile, PublicProfile } from '../api/profileTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { MoviePosterGrid } from '../components/profile/MoviePosterGrid'
import { readMyProfileBundleCache, writeMyProfileBundleCache } from '../lib/myProfileBundleCache'
import { displayNameFromProfile, profileInitials } from '../lib/profileDisplay'

type ProfileMainTab = 'movies' | 'stats'

function shownCount(value: number | undefined): string {
  return typeof value === 'number' ? String(value) : '0'
}

function toPublicShape(p: MyProfile): PublicProfile {
  return {
    id: p.id,
    profile_slug: p.profile_slug,
    username: p.username,
    first_name: p.first_name,
    last_name: p.last_name,
    photo_url: p.photo_url,
    display_name: p.display_name,
    bio: p.bio,
    cards_count: p.cards_count,
    friends_count: p.friends_count,
    followers_count: p.followers_count,
    following_count: p.following_count,
  }
}

export function ProfilePage() {
  const auth = useAuthStatus()
  const navigate = useNavigate()
  const initialBundle = useMemo(() => readMyProfileBundleCache(), [])

  const [mainTab, setMainTab] = useState<ProfileMainTab>('movies')
  const [profile, setProfile] = useState<MyProfile | null>(() => initialBundle?.profile ?? null)
  const [myCards, setMyCards] = useState<MovieCardPage | null>(() => initialBundle?.cards ?? null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [cardsError, setCardsError] = useState<string | null>(null)
  const [loadingMore, setLoadingMore] = useState(false)

  useEffect(() => {
    if (auth.kind !== 'ready') {
      return
    }
    let alive = true
    void (async () => {
      try {
        const p = await getMyProfile()
        if (!alive) {
          return
        }
        setProfile(p)
        const cards = await getUserCards(p.id, { limit: 20 })
        if (!alive) {
          return
        }
        setMyCards(cards)
        writeMyProfileBundleCache(p, cards)
        setLoadError(null)
        setCardsError(null)
      } catch (e) {
        if (!alive) {
          return
        }
        if (e instanceof ApiError) {
          setLoadError(formatApiDetail(e.detail))
        } else {
          setLoadError(e instanceof Error ? e.message : 'Ошибка загрузки')
        }
      }
    })()
    return () => {
      alive = false
    }
  }, [auth.kind])

  const loadMoreCards = useCallback(async () => {
    if (profile == null || myCards?.next_cursor == null || myCards.next_cursor === '') {
      return
    }
    setLoadingMore(true)
    setCardsError(null)
    try {
      const page = await getUserCards(profile.id, { cursor: myCards.next_cursor, limit: 20 })
      setMyCards((prev) => {
        if (prev == null) {
          writeMyProfileBundleCache(profile, page)
          return page
        }
        const next: MovieCardPage = {
          items: [...prev.items, ...page.items],
          next_cursor: page.next_cursor,
        }
        writeMyProfileBundleCache(profile, next)
        return next
      })
    } catch (e) {
      if (e instanceof ApiError) {
        setCardsError(formatApiDetail(e.detail))
      } else {
        setCardsError(e instanceof Error ? e.message : 'Ошибка загрузки')
      }
    } finally {
      setLoadingMore(false)
    }
  }, [profile, myCards])

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
          Откройте приложение в Telegram, чтобы увидеть профиль.
        </p>
        <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to="/">
          На главную
        </Link>
      </div>
    )
  }

  if (loadError != null) {
    return (
      <div className="mx-auto max-w-md px-4 py-12">
        <p className="filmony-text-panel text-sm text-(--tgui--destructive_text_color)">{loadError}</p>
        <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to="/">
          На главную
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

  const pub = toPublicShape(profile)
  const shownName = displayNameFromProfile(pub)
  const canLoadMore = Boolean(myCards?.next_cursor)
  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-20 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] backdrop-blur-md">
        <div className="flex items-center justify-between px-4 py-3">
          <h1 className="text-lg font-semibold tracking-tight text-(--tgui--text_color)">Профиль</h1>
          <Link
            to="/profile/edit"
            className="flex h-10 w-10 items-center justify-center rounded-xl text-lg text-(--tgui--link_color) no-underline active:opacity-70"
            aria-label="Настройки профиля"
          >
            ⚙
          </Link>
        </div>
      </header>

      <main className="px-4 py-6">
        <div className="flex flex-col items-center text-center">
          <Avatar
            src={profile.photo_url ?? undefined}
            acronym={profileInitials(pub)}
            size={96}
          />
          <Title className="mt-3" level="2" weight="2">
            {shownName}
          </Title>
          <p className="mt-1 font-mono text-[11px] text-(--tgui--hint_color)">@{profile.profile_slug}</p>
          <div className="mt-4 grid w-full max-w-sm grid-cols-3 gap-2">
            <button
              type="button"
              className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-2 py-2 text-center transition-opacity active:opacity-80"
              onClick={() => void navigate('/profile/subscriptions?tab=followers')}
            >
              <span className="block text-lg font-semibold tabular-nums">{shownCount(profile.followers_count)}</span>
              <span className="text-[11px] text-(--tgui--hint_color)">подписчиков</span>
            </button>
            <button
              type="button"
              className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-2 py-2 text-center transition-opacity active:opacity-80"
              onClick={() => void navigate('/profile/subscriptions?tab=following')}
            >
              <span className="block text-lg font-semibold tabular-nums">{shownCount(profile.following_count)}</span>
              <span className="text-[11px] text-(--tgui--hint_color)">подписок</span>
            </button>
            <div className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-2 py-2 text-center">
              <span className="block text-lg font-semibold tabular-nums">{profile.cards_count}</span>
              <span className="text-[11px] text-(--tgui--hint_color)">фильмов</span>
            </div>
          </div>
        </div>

        {profile.bio ? (
          <p className="filmony-text-panel mt-4 text-center text-sm leading-relaxed text-(--tgui--hint_color)">
            {profile.bio}
          </p>
        ) : null}

        <div className="mt-6 flex gap-1 rounded-full bg-(--tgui--secondary_bg_color) p-1">
          <button
            type="button"
            className={`flex flex-1 items-center justify-center gap-2 rounded-full py-2.5 text-sm font-medium transition-all ${
              mainTab === 'movies'
                ? 'bg-(--tgui--bg_color) text-(--tgui--text_color) shadow-sm'
                : 'text-(--tgui--hint_color)'
            }`}
            onClick={() => setMainTab('movies')}
          >
            Фильмы
          </button>
          <button
            type="button"
            className={`flex flex-1 items-center justify-center gap-2 rounded-full py-2.5 text-sm font-medium transition-all ${
              mainTab === 'stats'
                ? 'bg-(--tgui--bg_color) text-(--tgui--text_color) shadow-sm'
                : 'text-(--tgui--hint_color)'
            }`}
            onClick={() => setMainTab('stats')}
          >
            Статистика
          </button>
        </div>

        {mainTab === 'movies' ? (
          <div className="mt-6">
            {cardsError != null ? (
              <p className="filmony-text-panel mb-2 text-center text-sm text-(--tgui--destructive_text_color)">
                {cardsError}
              </p>
            ) : null}
            {myCards != null && myCards.items.length === 0 ? (
              <div className="filmony-text-panel py-8 text-center">
                <p className="text-sm text-(--tgui--hint_color)">Ещё нет оценённых фильмов</p>
              </div>
            ) : null}
            {myCards != null && myCards.items.length > 0 ? (
              <div className="px-1">
                <MoviePosterGrid items={myCards.items} />
              </div>
            ) : null}
            {canLoadMore ? (
              <div className="mt-4">
                <Button stretched disabled={loadingMore} onClick={() => void loadMoreCards()}>
                  {loadingMore ? 'Загрузка…' : 'Загрузить ещё'}
                </Button>
              </div>
            ) : null}
          </div>
        ) : null}

        {mainTab === 'stats' ? (
          <div className="mt-6 space-y-4">
            <div className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) p-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <p className="text-[11px] text-(--tgui--hint_color)">Фильмов оценено</p>
                  <p className="mt-1 text-2xl font-bold tabular-nums">{profile.cards_count}</p>
                </div>
                <div>
                  <p className="text-[11px] text-(--tgui--hint_color)">Друзей</p>
                  <p className="mt-1 text-2xl font-bold tabular-nums">{profile.friends_count}</p>
                </div>
              </div>
            </div>
            <Section header="Детали">
              <div className="filmony-text-panel mx-3 my-3 text-center text-sm leading-relaxed text-(--tgui--hint_color)">
                Распределение оценок, годы, теги и «с кем смотрел» появятся, когда бэкенд отдаст агрегаты по
                карточкам.
              </div>
            </Section>
          </div>
        ) : null}
      </main>

    </div>
  )
}
