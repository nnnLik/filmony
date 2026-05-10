import { Button } from '@telegram-apps/telegram-ui'
import { Share2 } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'

import { ApiError, formatApiDetail } from '../api/client'
import { getMovieCardById, shareMovieCardWithFollowers } from '../api/cardApi'
import { getMyProfile, getUserSubscriptions } from '../api/profileApi'
import type { MovieCard, SubscriptionListItem } from '../api/profileTypes'
import { ShareFollowersPicker } from '../components/share/ShareFollowersPicker'
import { buildMiniAppCardDeepLink } from '../lib/miniAppCardDeepLink'
import { useAuthStatus } from '../auth/useAuthStatus'

const MAX_SHARE_COMMENT_LEN = 500

type ShareMovieCardLocationState = {
  shareOpenedFromCardDetail?: boolean
}

export function ShareMovieCardPage() {
  const auth = useAuthStatus()
  const navigate = useNavigate()
  const location = useLocation()
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
  const [shareComment, setShareComment] = useState('')

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
      } catch (error: unknown) {
        if (!alive) return
        setError(error instanceof ApiError ? formatApiDetail(error.detail) : 'Не удалось загрузить данные')
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
      await shareMovieCardWithFollowers(parsedId, Array.from(selected), {
        shareComment: shareComment.slice(0, MAX_SHARE_COMMENT_LEN),
      })
      setSelected(new Set())
      const openedFromCardDetail =
        (location.state as ShareMovieCardLocationState | null)?.shareOpenedFromCardDetail === true
      if (openedFromCardDetail) {
        void navigate(-1)
      } else {
        void navigate(`/cards/${parsedId}`, { replace: true })
      }
    } catch (error: unknown) {
      setError(error instanceof ApiError ? formatApiDetail(error.detail) : 'Не удалось отправить')
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
            <ShareFollowersPicker
              preview={{
                posterUrl: card.film_poster_url,
                title: card.film_title,
                yearLabel: card.film_year != null ? String(card.film_year) : '—',
              }}
              followers={followers}
              loading={false}
              selected={selected}
              onToggle={toggle}
              deepLinkToCopy={buildMiniAppCardDeepLink(parsedId)}
            />

            <div className="mt-4">
              <p className="text-sm font-medium text-(--tgui--text_color)">Комментарий к уведомлению</p>
              <p className="mt-1 text-xs text-(--tgui--hint_color)">
                Текст уйдёт в Telegram вместе с карточкой. До {MAX_SHARE_COMMENT_LEN} символов.
              </p>
              <textarea
                value={shareComment}
                maxLength={MAX_SHARE_COMMENT_LEN}
                onChange={(e) => setShareComment(e.currentTarget.value)}
                placeholder="Например: обязательно откройте в приложении…"
                rows={3}
                className="mt-2 min-h-20 w-full resize-y rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-3 py-2.5 text-sm text-(--tgui--text_color) outline-none placeholder:text-(--tgui--hint_color) focus-visible:border-(--tgui--link_color) focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--tgui--link_color)_32%,transparent)]"
              />
              <p className="mt-1 text-xs text-(--tgui--hint_color)">
                {shareComment.length}/{MAX_SHARE_COMMENT_LEN}
              </p>
            </div>

            {error != null ? (
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
