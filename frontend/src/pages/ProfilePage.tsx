import { Avatar, Button, Cell, Input, List, Section, Title } from '@telegram-apps/telegram-ui'
import { type ChangeEvent, type FormEvent, useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { ApiError, formatApiDetail } from '../api/client'
import { getMyProfile, getUserCards, patchMyProfile } from '../api/profileApi'
import type { MovieCardPage, MyProfile, PublicProfile } from '../api/profileTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { displayNameFromProfile, profileInitials } from '../lib/profileDisplay'

type ProfileMainTab = 'movies' | 'stats'

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
  }
}

export function ProfilePage() {
  const auth = useAuthStatus()
  const [mainTab, setMainTab] = useState<ProfileMainTab>('movies')
  const [profile, setProfile] = useState<MyProfile | null>(null)
  const [myCards, setMyCards] = useState<MovieCardPage | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [cardsError, setCardsError] = useState<string | null>(null)
  const [loadingMore, setLoadingMore] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  const [displayName, setDisplayName] = useState('')
  const [bio, setBio] = useState('')
  const [slug, setSlug] = useState('')

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
        setDisplayName(p.display_name ?? '')
        setBio(p.bio ?? '')
        setSlug(p.profile_slug)
        const cards = await getUserCards(p.id, { limit: 20 })
        if (!alive) {
          return
        }
        setMyCards(cards)
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
        setCardsError(e instanceof Error ? e.message : 'Ошибка загрузки')
      }
    } finally {
      setLoadingMore(false)
    }
  }, [profile, myCards])

  async function saveProfile() {
    setSaveError(null)
    setSaving(true)
    try {
      const next = await patchMyProfile({
        display_name: displayName.trim() || null,
        bio: bio.trim() || null,
        profile_slug: slug.trim(),
      })
      setProfile(next)
      setSlug(next.profile_slug)
    } catch (err) {
      if (err instanceof ApiError) {
        setSaveError(formatApiDetail(err.detail))
      } else {
        setSaveError(err instanceof Error ? err.message : 'Не удалось сохранить')
      }
    } finally {
      setSaving(false)
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    void saveProfile()
  }

  if (auth.kind === 'loading') {
    return (
      <div className="px-4 py-16 text-center text-sm text-(--tgui--hint_color)">
        <p>Вход…</p>
      </div>
    )
  }

  if (auth.kind === 'error') {
    return (
      <div className="mx-auto max-w-md px-4 py-12">
        <p className="text-sm text-red-500">{auth.message}</p>
        <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to="/">
          На главную
        </Link>
      </div>
    )
  }

  if (auth.kind === 'skipped') {
    return (
      <div className="mx-auto max-w-md px-4 py-12">
        <p className="text-sm text-(--tgui--hint_color)">
          Откройте приложение в Telegram, чтобы увидеть профиль и сохранять изменения.
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
        <p className="text-sm text-red-500">{loadError}</p>
        <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to="/">
          На главную
        </Link>
      </div>
    )
  }

  if (profile == null) {
    return (
      <div className="px-4 py-16 text-center text-sm text-(--tgui--hint_color)">
        <p>Загрузка…</p>
      </div>
    )
  }

  const pub = toPublicShape(profile)
  const shownName = displayNameFromProfile(pub)
  const canLoadMore = Boolean(myCards?.next_cursor)

  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-20 border-b border-(--tgui--divider_color) bg-(--tgui--bg_color)/95 backdrop-blur-md">
        <div className="flex items-center justify-between px-4 py-3">
          <h1 className="text-lg font-semibold tracking-tight">Профиль</h1>
          <Button mode="plain" size="s" disabled title="Скоро">
            ⚙
          </Button>
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
          <Button mode="gray" className="mt-3" disabled>
            {profile.friends_count} друзей
          </Button>
        </div>

        {profile.bio ? (
          <p className="mt-4 text-center text-sm leading-relaxed text-(--tgui--hint_color)">{profile.bio}</p>
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
            {cardsError != null ? <p className="mb-2 text-center text-sm text-red-500">{cardsError}</p> : null}
            {myCards != null && myCards.items.length === 0 ? (
              <div className="py-12 text-center">
                <p className="text-sm text-(--tgui--hint_color)">Ещё нет оценённых фильмов</p>
                <p className="mt-2 text-xs text-(--tgui--hint_color)">Карточки появятся после фичи каталога.</p>
              </div>
            ) : null}
            {myCards != null && myCards.items.length > 0 ? (
              <List>
                {myCards.items.map((_, i) => (
                  <Cell key={i} subtitle="Скоро">
                    Карточка
                  </Cell>
                ))}
              </List>
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
              <div className="px-3 py-4 text-center text-sm leading-relaxed text-(--tgui--hint_color)">
                Распределение оценок, годы, теги и «с кем смотрел» появятся, когда бэкенд отдаст агрегаты по
                карточкам.
              </div>
            </Section>
          </div>
        ) : null}

        <Section className="mt-8" header="Редактирование">
          <form className="flex flex-col gap-3 px-3 pb-4 pt-1" onSubmit={handleSubmit}>
            <Input
              header="Отображаемое имя"
              placeholder={displayNameFromProfile(pub)}
              value={displayName}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setDisplayName(e.target.value)}
            />
            <div className="flex flex-col gap-1">
              <span className="px-3 text-xs font-medium uppercase tracking-wide text-(--tgui--hint_color)">
                О себе
              </span>
              <textarea
                className="min-h-[88px] rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-3 py-2 text-(--tgui--text_color) outline-none"
                maxLength={500}
                placeholder="Коротко о вкусе"
                value={bio}
                onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setBio(e.target.value)}
              />
            </div>
            <Input
              header="Публичная ссылка (/u/…)"
              placeholder="например, kino-ivan"
              value={slug}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setSlug(e.target.value)}
            />
            {saveError != null ? <p className="text-sm text-red-500">{saveError}</p> : null}
            <div className="flex flex-col gap-2">
              <Button type="submit" disabled={saving} stretched>
                {saving ? 'Сохранение…' : 'Сохранить'}
              </Button>
              <Link
                className="flex h-12 items-center justify-center rounded-xl bg-(--tgui--secondary_bg_color) text-sm font-medium text-(--tgui--link_color) no-underline active:opacity-80"
                to={`/u/${profile.profile_slug}`}
              >
                Как видят другие
              </Link>
            </div>
          </form>
        </Section>
      </main>
    </div>
  )
}
