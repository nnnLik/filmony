import { Button, Section, Title } from '@telegram-apps/telegram-ui'
import { useQuery } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'

import { getFilmById, getFilmCommunityCardsPage, getFollowingRatingsForFilm } from '../api/cardApi'
import { getMyWeeklyControversy } from '../api/controversyApi'
import { ApiError, formatApiDetail } from '../api/client'
import {
  deleteMyWatchlistFilm,
  getMyPlannedCard,
  getMyProfile,
  getMyWatchlistPresence,
} from '../api/profileApi'
import type { Film, FilmCommunityCardItem } from '../api/profileTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { CommunityRatingsList } from '../components/catalog/CommunityRatingsList'
import { FollowingRatingsPanel } from '../components/social/FollowingRatingsPanel'
import { FilmGenreChips } from '../components/films/FilmGenreChips'
import { DirectorChip } from '../components/films/DirectorChip'
import { FranchiseChip } from '../components/films/FranchiseChip'
import {
  buildFollowingRatingDisplayRows,
  type FollowingRatingRow,
} from '../lib/followingRatingsDisplay'
import { WatchlistOverlapAnchorBanner } from '../components/watchlist/WatchlistOverlapSection'
import { formatRating } from '../components/feed/feedCardUtils'
import { useTasteQuizKnowledgeOfUsers } from '../hooks/useTasteQuizKnowledgeOfUsers'
import { useRatingStreaksOfUsers } from '../hooks/useRatingStreaksOfUsers'
import { clearMyProfileBundleCache, readMyProfileBundleCache } from '../lib/myProfileBundleCache'

export function FilmDetailPage() {
  const auth = useAuthStatus()
  const navigate = useNavigate()
  const { filmId: filmIdRaw } = useParams<{ filmId: string }>()
  const parsedId = Number(filmIdRaw)
  const filmId = Number.isInteger(parsedId) && parsedId >= 1 ? parsedId : 0

  const [film, setFilm] = useState<Film | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [inWatchlist, setInWatchlist] = useState<boolean | null>(null)
  const [plannedUserCardId, setPlannedUserCardId] = useState<number | null>(null)
  const [removeBusy, setRemoveBusy] = useState(false)
  const [watchlistActionErr, setWatchlistActionErr] = useState<string | null>(null)

  const [community, setCommunity] = useState<FilmCommunityCardItem[]>([])
  const [communityNext, setCommunityNext] = useState<string | null>(null)
  const [communityLoading, setCommunityLoading] = useState(false)
  const [communityErr, setCommunityErr] = useState<string | null>(null)
  const [communityMoreBusy, setCommunityMoreBusy] = useState(false)
  const [followingRatings, setFollowingRatings] = useState<FollowingRatingRow[] | null>(null)
  const [viewerId, setViewerId] = useState<string | null>(() => readMyProfileBundleCache()?.profile.id ?? null)

  const communityAuthorIds = useMemo(
    () => community.map((row) => row.author.id),
    [community],
  )
  const { knowledgeByOwnerId: tasteQuizKnowledgeByAuthor } = useTasteQuizKnowledgeOfUsers(
    communityAuthorIds,
    { enabled: auth.kind === 'ready' && communityAuthorIds.length > 0 },
  )
  const { streakByUserId } = useRatingStreaksOfUsers(communityAuthorIds, {
    enabled: auth.kind === 'ready' && communityAuthorIds.length > 0,
  })
  const [descExpanded, setDescExpanded] = useState(false)

  const controversyQuery = useQuery({
    queryKey: ['weeklyControversy'],
    queryFn: getMyWeeklyControversy,
    enabled: auth.kind === 'ready' && filmId >= 1,
    staleTime: 5 * 60_000,
    gcTime: 10 * 60_000,
  })

  const weeklyControversyForFilm = useMemo(() => {
    const controversy = controversyQuery.data?.controversy
    if (controversy == null || film == null) return null
    if (controversy.anchor_film_id != null && controversy.anchor_film_id === film.id) {
      return controversy
    }
    return null
  }, [controversyQuery.data, film])

  useEffect(() => {
    let alive = true
    void (async () => {
      await Promise.resolve()
      if (!alive) return
      setWatchlistActionErr(null)
      if (filmId < 1) {
        setError('Некорректный id в каталоге')
        setLoading(false)
        setFilm(null)
        return
      }
      setLoading(true)
      setError(null)
      try {
        const f = await getFilmById(filmId)
        if (!alive) return
        setFilm(f)
      } catch (e) {
        if (!alive) return
        if (e instanceof ApiError && e.status === 404) {
          setError('Запись в каталоге не найдена.')
        } else if (e instanceof ApiError) {
          setError(formatApiDetail(e.detail))
        } else {
          setError('Не удалось загрузить запись каталога')
        }
        setFilm(null)
      } finally {
        if (alive) setLoading(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [filmId])

  useEffect(() => {
    if (film == null || filmId < 1) {
      queueMicrotask(() => {
        setCommunity([])
        setCommunityNext(null)
        setCommunityErr(null)
        setCommunityLoading(false)
      })
      return
    }
    let alive = true
    queueMicrotask(() => {
      if (!alive) return
      setCommunityLoading(true)
      setCommunityErr(null)
      void getFilmCommunityCardsPage(filmId, { limit: 25 })
        .then((page) => {
          if (!alive) return
          setCommunity(page.items)
          setCommunityNext(page.next_cursor)
        })
        .catch((e: unknown) => {
          if (!alive) return
          setCommunity([])
          setCommunityNext(null)
          setCommunityErr(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось загрузить оценки')
        })
        .finally(() => {
          if (alive) setCommunityLoading(false)
        })
    })
    return () => {
      alive = false
    }
  }, [film, filmId])

  useEffect(() => {
    if (auth.kind !== 'ready' || filmId < 1) {
      queueMicrotask(() => setFollowingRatings(null))
      return
    }
    let alive = true
    queueMicrotask(() => {
      if (alive) setFollowingRatings(null)
    })
    void getFollowingRatingsForFilm(filmId)
      .then((data) => {
        if (!alive) return
        setFollowingRatings(buildFollowingRatingDisplayRows(data.viewer_rating ?? null, data.items))
      })
      .catch(() => {
        if (!alive) return
        setFollowingRatings([])
      })
    return () => {
      alive = false
    }
  }, [auth.kind, filmId])

  useEffect(() => {
    let alive = true
    void (async () => {
      if (auth.kind !== 'ready' || film == null || film.kinopoisk_id < 1) {
        queueMicrotask(() => {
          if (auth.kind !== 'ready') setInWatchlist(null)
        })
        return
      }
      try {
        const cardId = `kp:${film.kinopoisk_id}`
        const m = await getMyWatchlistPresence(cardId)
        if (!alive) return
        setInWatchlist(m.in_watchlist)
        if (m.in_watchlist) {
          try {
            const planned = await getMyPlannedCard({ film_id: film.id })
            if (!alive) return
            setPlannedUserCardId(planned.user_card_id)
          } catch {
            if (!alive) return
            setPlannedUserCardId(null)
          }
        } else {
          setPlannedUserCardId(null)
        }
      } catch {
        if (!alive) return
        setInWatchlist(false)
        setPlannedUserCardId(null)
      }
    })()
    return () => {
      alive = false
    }
  }, [auth.kind, film])

  const filmOverlapAnchor = useMemo(
    () =>
      film != null
        ? {
            card_id: film.kinopoisk_id > 0 ? `kp:${film.kinopoisk_id}` : null,
            film_id: film.id,
          }
        : null,
    [film],
  )

  const hasMyRatedCard = film != null && film.my_card_id != null && film.my_card_id > 0

  const onAddToWatchlist = useCallback(() => {
    if (filmId < 1 || film == null) return
    void navigate(`/watchlist/new?filmId=${encodeURIComponent(String(film.id))}`)
  }, [film, filmId, navigate])

  const onRemoveFromWatchlist = useCallback(async () => {
    if (filmId < 1) return
    setRemoveBusy(true)
    setWatchlistActionErr(null)
    try {
      await deleteMyWatchlistFilm(filmId)
      setInWatchlist(false)
      clearMyProfileBundleCache()
    } catch (e) {
      if (e instanceof ApiError) {
        setWatchlistActionErr(formatApiDetail(e.detail))
      } else {
        setWatchlistActionErr('Не удалось убрать из списка')
      }
    } finally {
      setRemoveBusy(false)
    }
  }, [filmId])

  useEffect(() => {
    if (viewerId != null) return
    let alive = true
    void (async () => {
      try {
        const profile = await getMyProfile()
        if (!alive) return
        setViewerId(profile.id)
      } catch {
        void 0
      }
    })()
    return () => {
      alive = false
    }
  }, [viewerId])

  const loadMoreCommunity = useCallback(async () => {
    if (filmId < 1 || communityNext == null) return
    setCommunityMoreBusy(true)
    try {
      const page = await getFilmCommunityCardsPage(filmId, { cursor: communityNext, limit: 25 })
      setCommunity((prev) => [...prev, ...page.items])
      setCommunityNext(page.next_cursor)
    } catch (e) {
      setCommunityErr(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось подгрузить оценки')
    } finally {
      setCommunityMoreBusy(false)
    }
  }, [filmId, communityNext])

  if (auth.kind === 'loading' || auth.kind === 'skipped') {
    return (
      <div className="min-h-dvh bg-(--tgui--bg_color) px-4 py-16 text-center text-sm text-(--tgui--hint_color)">
        <p className="filmony-text-panel inline-block">Вход…</p>
      </div>
    )
  }

  if (auth.kind === 'error') {
    return (
      <div className="min-h-dvh bg-(--tgui--bg_color) px-4 py-12">
        <p className="filmony-text-panel text-sm text-(--tgui--destructive_text_color)">{auth.message}</p>
        <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to="/">
          На главную
        </Link>
      </div>
    )
  }

  const longDescription = film?.description?.trim() ?? ''

  return (
    <div className="min-h-dvh bg-(--tgui--bg_color) pb-8 text-(--tgui--text_color)">
      <header className="sticky top-0 z-20 flex items-center gap-2 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] px-2 py-2 backdrop-blur-md">
        <button
          type="button"
          className="flex min-h-10 min-w-10 items-center justify-center rounded-lg text-lg text-(--tgui--link_color)"
          aria-label="Назад"
          onClick={() => {
            void navigate(-1)
          }}
        >
          ←
        </button>
        <span className="truncate text-sm font-medium text-(--tgui--hint_color)">Тема в каталоге</span>
      </header>

      <main className="mx-auto max-w-md space-y-4 px-4 pt-4">
        {loading ? (
          <p className="filmony-text-panel py-12 text-center text-sm text-(--tgui--hint_color)">Загрузка…</p>
        ) : null}
        {!loading && error != null ? (
          <div className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-4 py-4">
            <p className="text-sm text-(--tgui--hint_color)">{error}</p>
            <Button className="mt-4" stretched onClick={() => void navigate('/')}>
              На главную
            </Button>
          </div>
        ) : null}
        {!loading && error == null && film != null ? (
          <>
            <Section header={film.title}>
              <div className="px-3 py-3">
                <div className="filmony-text-panel flex gap-3">
                  <div className="h-40 w-28 shrink-0 overflow-hidden rounded-xl bg-(--tgui--secondary_bg_color)">
                    {film.poster_url ? (
                      <img src={film.poster_url} alt={film.title} className="h-full w-full object-cover" />
                    ) : null}
                  </div>
                  <div className="min-w-0">
                    <Title level="3" weight="2">
                      {film.title}
                    </Title>
                    <p className="mt-1 text-sm text-(--tgui--hint_color)">{film.year ?? 'Год неизвестен'}</p>
                    {film.primary_director_kinopoisk_id != null &&
                    film.primary_director_name != null &&
                    film.primary_director_name.trim() !== '' ? (
                      <DirectorChip
                        kinopoiskId={film.primary_director_kinopoisk_id}
                        name={film.primary_director_name}
                        size="md"
                        className="mt-2"
                      />
                    ) : null}
                    {film.franchise_key != null &&
                    film.franchise_label != null &&
                    film.franchise_label.trim() !== '' ? (
                      <FranchiseChip
                        franchiseKey={film.franchise_key}
                        label={film.franchise_label}
                        size="md"
                        className="mt-2"
                      />
                    ) : null}
                    <FilmGenreChips genres={film.genres} size="md" className="mt-2" />
                    {weeklyControversyForFilm != null ? (
                      <span
                        className="mt-2 inline-flex max-w-full items-center rounded-md border border-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_42%,transparent)] bg-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_12%,transparent)] px-2 py-1 text-[11px] font-semibold text-(--tgui--text_color)"
                        title={`Недельный спор: ${weeklyControversyForFilm.title}`}
                      >
                        Разброс {formatRating(weeklyControversyForFilm.spread)} · {weeklyControversyForFilm.rater_count}{' '}
                        друзей
                      </span>
                    ) : null}
                  </div>
                </div>

                {(film.short_description?.trim() || longDescription) ? (
                  <div className="mt-4 border-t border-(--tgui--divider_color) pt-4">
                    {film.short_description?.trim() ? (
                      <p className="text-[14px] leading-relaxed text-(--tgui--text_color)">
                        {film.short_description.trim()}
                      </p>
                    ) : null}
                    {longDescription ? (
                      <div className={film.short_description?.trim() ? 'mt-3' : ''}>
                        <p
                          className={`text-[14px] leading-relaxed text-(--tgui--text_color) ${
                            !descExpanded ? 'line-clamp-6' : ''
                          }`}
                        >
                          {longDescription}
                        </p>
                        {longDescription.length > 320 ? (
                          <button
                            type="button"
                            className="mt-2 text-sm font-medium text-(--tgui--link_color)"
                            onClick={() => setDescExpanded((v) => !v)}
                          >
                            {descExpanded ? 'Свернуть описание' : 'Полное описание'}
                          </button>
                        ) : null}
                      </div>
                    ) : null}
                  </div>
                ) : null}

                {auth.kind === 'ready' ? (
                  <div className="mt-6 flex flex-col gap-2">
                    <WatchlistOverlapAnchorBanner
                      anchor={filmOverlapAnchor}
                      enabled={!hasMyRatedCard}
                      inViewerWatchlist={inWatchlist}
                    />
                    {hasMyRatedCard ? (
                      <>
                        <p className="text-sm text-(--tgui--hint_color)">
                          Эта тема уже в ваших оценённых карточках.
                        </p>
                        <Link
                          to={`/cards/${encodeURIComponent(String(film.my_card_id))}`}
                          className="no-underline"
                        >
                          <Button stretched>Открыть мою карточку</Button>
                        </Link>
                        <Link
                          to={`/cards/${encodeURIComponent(String(film.my_card_id))}/edit`}
                          className="no-underline"
                        >
                          <Button mode="gray" stretched>
                            Редактировать оценку
                          </Button>
                        </Link>
                      </>
                    ) : (
                      <>
                        <Link to={`/cards/new?filmId=${encodeURIComponent(String(film.id))}`} className="no-underline">
                          <Button stretched>Добавить карточку с оценкой</Button>
                        </Link>
                        {inWatchlist === false ? (
                          <Button mode="gray" stretched onClick={onAddToWatchlist}>
                            В список «Позже»
                          </Button>
                        ) : null}
                        {inWatchlist === true ? (
                          <>
                            {plannedUserCardId != null && plannedUserCardId > 0 ? (
                              <Link
                                to={`/cards/${encodeURIComponent(String(plannedUserCardId))}`}
                                className="no-underline"
                              >
                                <Button stretched>Открыть запланированную карточку</Button>
                              </Link>
                            ) : null}
                            <Button
                              mode="gray"
                              stretched
                              disabled={removeBusy}
                              onClick={() => void onRemoveFromWatchlist()}
                            >
                              {removeBusy ? 'Убираем…' : 'Убрать из списка «Позже»'}
                            </Button>
                          </>
                        ) : null}
                      </>
                    )}
                    {watchlistActionErr != null ? (
                      <p className="text-sm text-(--tgui--destructive_text_color)">{watchlistActionErr}</p>
                    ) : null}
                  </div>
                ) : null}
              </div>
            </Section>

            {auth.kind === 'ready' ? (
              <FollowingRatingsPanel rows={followingRatings} />
            ) : null}

            <Section header="Оценки в Filmony">
              <CommunityRatingsList
                items={community}
                loading={communityLoading}
                error={communityErr}
                nextCursor={communityNext}
                moreBusy={communityMoreBusy}
                viewerId={viewerId}
                tasteQuizKnowledgeByAuthor={tasteQuizKnowledgeByAuthor}
                streakByUserId={streakByUserId}
                onLoadMore={() => void loadMoreCommunity()}
              />
            </Section>
          </>
        ) : null}
      </main>
    </div>
  )
}
