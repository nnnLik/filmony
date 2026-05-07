import { Avatar, Button, Title } from '@telegram-apps/telegram-ui'
import { Share2 } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { ApiError, formatApiDetail } from '../api/client'
import { getMovieCardById, shareMovieCardWithFollowers } from '../api/cardApi'
import { getMyProfile, getUserSubscriptions } from '../api/profileApi'
import type { MovieCard, PublicProfile, SubscriptionListItem } from '../api/profileTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { displayNameFromProfile, profileInitials } from '../lib/profileDisplay'

function toPublicFromSubscription(row: SubscriptionListItem): PublicProfile {
  return {
    id: row.id,
    profile_slug: row.profile_slug,
    username: row.username,
    first_name: row.first_name,
    last_name: row.last_name,
    photo_url: row.photo_url,
    display_name: row.display_name,
    bio: null,
    cards_count: 0,
    friends_count: 0,
    followers_count: 0,
    following_count: 0,
  }
}

export function ShareMovieCardPage() {
  const auth = useAuthStatus()
  const navigate = useNavigate()
  const { cardId } = useParams<{ cardId?: string }>()
  const parsedId = useMemo(() => {
    if (cardId == null) return null
    const n = Number(cardId)
    return Number.isInteger(n) && n > 0 ? n : null
  }, [cardId])

  const [card, setCard] = useState<MovieCard | null>(null)
  const [followers, setFollowers] = useState<SubscriptionListItem[]>([])
  const [selected, setSelected] = useState<Set<string>>(() => new Set())
  const [loading, setLoading] = useState(true)
  const [submitBusy, setSubmitBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (auth.kind !== 'ready' || parsedId == null) return
    let alive = true
    void (async () => {
      setLoading(true)
      setError(null)
      try {
        const me = await getMyProfile()
        if (!alive) return
        const c = await getMovieCardById(parsedId)
        if (!alive) return
        if (c.user_id !== me.id) {
          setError('Поделиться можно только своей карточкой')
          setCard(null)
          return
        }
        setCard(c)
        const subs = await getUserSubscriptions(me.id, 'followers')
        if (!alive) return
        setFollowers(subs.items.filter((x) => x.relation_type === 'follower'))
      } catch (e) {
        if (!alive) return
        setError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось загрузить данные')
      } finally {
        if (alive) setLoading(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [auth.kind, parsedId])

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  async function submitShare() {
    if (parsedId == null || selected.size === 0) return
    setSubmitBusy(true)
    setError(null)
    try {
      await shareMovieCardWithFollowers(parsedId, [...selected])
      setSelected(new Set())
      void navigate(`/cards/${parsedId}`)
    } catch (e) {
      setError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось отправить')
    } finally {
      setSubmitBusy(false)
    }
  }

  if (auth.kind === 'loading' || auth.kind === 'error' || auth.kind === 'skipped') {
    return (
      <div className="px-4 py-16 text-center text-sm text-(--tgui--hint_color)">
        <p className="filmony-text-panel inline-block">Загрузка…</p>
      </div>
    )
  }

  if (parsedId == null) {
    return (
      <div className="mx-auto max-w-md px-4 py-12">
        <p className="filmony-text-panel text-sm text-(--tgui--destructive_text_color)">Некорректная карточка</p>
        <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to="/profile">
          В профиль
        </Link>
      </div>
    )
  }

  return (
    <div className="min-h-dvh bg-(--tgui--bg_color) text-(--tgui--text_color)">
      <header className="sticky top-0 z-20 flex items-center gap-2 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] px-2 py-2 backdrop-blur-md">
        <button
          type="button"
          className="flex min-h-10 min-w-10 items-center justify-center rounded-xl text-lg text-(--tgui--link_color)"
          aria-label="Назад"
          onClick={() => void navigate(-1)}
        >
          ←
        </button>
        <Share2 className="size-5 shrink-0 text-(--tgui--link_color)" aria-hidden />
        <h1 className="min-w-0 flex-1 truncate text-base font-semibold tracking-tight text-(--tgui--text_color)">
          Поделиться карточкой
        </h1>
      </header>

      <main className="mx-auto max-w-md px-4 py-4">
        {loading ? (
          <p className="filmony-text-panel py-10 text-center text-sm text-(--tgui--hint_color)">Загрузка…</p>
        ) : null}

        {!loading && error != null && card == null ? (
          <div className="py-8 text-center">
            <p className="filmony-text-panel text-sm text-(--tgui--destructive_text_color)">{error}</p>
            <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to={`/cards/${parsedId}`}>
              К карточке
            </Link>
          </div>
        ) : null}

        {!loading && card != null ? (
          <div className="space-y-4">
            <div className="overflow-hidden rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color)">
              <div className="aspect-video w-full">
                {card.film_poster_url ? (
                  <img src={card.film_poster_url} alt="" className="h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full items-center justify-center text-sm text-(--tgui--hint_color)">Нет постера</div>
                )}
              </div>
              <div className="px-4 py-3">
                <Title level="3" weight="2" className="line-clamp-2">
                  {card.film_title}
                </Title>
                <p className="mt-1 text-sm text-(--tgui--hint_color)">{card.film_year ?? '—'}</p>
              </div>
            </div>

            <p className="filmony-text-panel text-sm leading-relaxed text-(--tgui--hint_color)">
              Выберите подписчиков — им уйдёт сообщение в Telegram с постером, оценкой и тегами карточки.
            </p>

            {followers.length === 0 ? (
              <p className="filmony-text-panel text-center text-sm text-(--tgui--hint_color)">
                Пока нет подписчиков. Когда кто-то подпишется на вас, вы сможете делиться здесь.
              </p>
            ) : (
              <ul className="flex flex-col gap-2">
                {followers.map((row) => {
                  const pub = toPublicFromSubscription(row)
                  const name = displayNameFromProfile(pub)
                  const checked = selected.has(row.id)
                  return (
                    <li key={row.id}>
                      <button
                        type="button"
                        onClick={() => toggle(row.id)}
                        className={`flex w-full items-center gap-3 rounded-2xl border px-3 py-2.5 text-left transition ${
                          checked
                            ? 'border-(--tgui--link_color) bg-[color-mix(in_srgb,var(--tgui--link_color)_12%,var(--tgui--secondary_bg_color))]'
                            : 'border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color)'
                        }`}
                      >
                        <span className="flex size-5 shrink-0 items-center justify-center rounded border border-(--tgui--divider_color) bg-(--tgui--bg_color)">
                          {checked ? <span className="text-xs text-(--tgui--link_color)">✓</span> : null}
                        </span>
                        <Avatar src={row.photo_url ?? undefined} acronym={profileInitials(pub)} size={40} />
                        <span className="min-w-0 flex-1 truncate text-sm font-medium">{name}</span>
                      </button>
                    </li>
                  )
                })}
              </ul>
            )}

            {error != null && card != null ? (
              <p className="filmony-text-panel text-center text-sm text-(--tgui--destructive_text_color)">{error}</p>
            ) : null}

            {followers.length > 0 ? (
              <Button stretched disabled={submitBusy || selected.size === 0} onClick={() => void submitShare()}>
                {submitBusy ? 'Отправка…' : `Поделиться${selected.size > 0 ? ` (${selected.size})` : ''}`}
              </Button>
            ) : null}
          </div>
        ) : null}
      </main>
    </div>
  )
}
