import { Button } from '@telegram-apps/telegram-ui'
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
import { TitleCommunityDetailLayout } from '../components/catalog/TitleCommunityDetailLayout'
import { PageErrorState } from '../components/ui/PageErrorState'
import { PageLoadingState } from '../components/ui/PageLoadingState'
import { FollowingRatingsPanel } from '../components/social/FollowingRatingsPanel'
import { FilmGenreChips } from '../components/films/FilmGenreChips'
import { OscarReleaseYearRow } from '../components/films/OscarReleaseYearLabel'
import { releaseYearLabel } from '../lib/filmAwardBadgeDisplay'
import { DirectorChip } from '../components/films/DirectorChip'
import { FranchiseChip } from '../components/films/FranchiseChip'
import {
  buildFollowingRatingDisplayRows,
  type FollowingRatingRow,
} from '../lib/followingRatingsDisplay'
import { WatchlistOverlapAnchorBanner } from '../components/watchlist/WatchlistOverlapSection'
import { useTasteQuizKnowledgeOfUsers } from '../hooks/useTasteQuizKnowledgeOfUsers'
import { useRatingStreaksOfUsers } from '../hooks/useRatingStreaksOfUsers'
import { useWatchingNowOfUsers } from '../hooks/useWatchingNowOfUsers'
import { clearMyProfileBundleCache, readMyProfileBundleCache } from '../lib/myProfileBundleCache'
import { formatRating } from '../components/feed/feedCardUtils'

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
  const { watchingByUserId } = useWatchingNowOfUsers(communityAuthorIds, {
    enabled: auth.kind === 'ready' && communityAuthorIds.length > 0,
    staleTime: 60_000,
    refetchInterval: 60_000,
  })
  const followingUserIds = useMemo(() => {
    if (followingRatings == null) return undefined
    const ids = new Set<string>()
    for (const row of followingRatings) {
      if (row.is_viewer !== true) {
        ids.add(row.user_id)
      }
    }
    return ids
  }, [followingRatings])
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

  if (auth.kind === 'loading') {
    return <PageLoadingState authPending className="bg-(--tgui--bg_color)" />
  }

  if (auth.kind === 'error') {
    return (
      <PageErrorState
        message={auth.message}
        backHref="/"
        backLabel="На главную"
        className="bg-(--tgui--bg_color)"
      />
    )
  }

  const titleMeta = film != null ? (
    <>
      <OscarReleaseYearRow
        label={releaseYearLabel(film.year)}
        badges={film.award_badges ?? []}
        releaseYear={film.year}
        variant="inline"
        className="mt-1"
      />
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
      {film.franchise_key != null && film.franchise_label != null && film.franchise_label.trim() !== '' ? (
        <FranchiseChip franchiseKey={film.franchise_key} label={film.franchise_label} size="md" className="mt-2" />
      ) : null}
      <FilmGenreChips genres={film.genres} size="md" className="mt-2" />
      {weeklyControversyForFilm != null ? (
        <span
          className="mt-2 inline-flex max-w-full items-center rounded-md border border-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_42%,transparent)] bg-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_12%,transparent)] px-2 py-1 text-[11px] font-semibold text-(--tgui--text_color)"
          title={`Недельный спор: ${weeklyControversyForFilm.title}`}
        >
          Разброс {formatRating(weeklyControversyForFilm.spread)} · {weeklyControversyForFilm.rater_count} друзей
        </span>
      ) : null}
    </>
  ) : null

  const watchlistActions =
    auth.kind === 'ready' && film != null ? (
      <>
        {film.kinopoisk_id >= 1 ? (
          <>
            <Link to={`/films/${encodeURIComponent(String(film.id))}/watch`} className="no-underline">
              <Button stretched>Смотреть</Button>
            </Link>
          </>
        ) : null}
        {hasMyRatedCard ? (
          <>
            <p className="text-sm text-(--tgui--hint_color)">Эта тема уже в ваших оценённых карточках.</p>
            <Link to={`/cards/${encodeURIComponent(String(film.my_card_id))}`} className="no-underline">
              <Button stretched>Открыть мою карточку</Button>
            </Link>
            <Link to={`/cards/${encodeURIComponent(String(film.my_card_id))}/edit`} className="no-underline">
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
                  <Link to={`/cards/${encodeURIComponent(String(plannedUserCardId))}`} className="no-underline">
                    <Button stretched>Открыть запланированную карточку</Button>
                  </Link>
                ) : null}
                <Button mode="gray" stretched disabled={removeBusy} onClick={() => void onRemoveFromWatchlist()}>
                  {removeBusy ? 'Убираем…' : 'Убрать из списка «Позже»'}
                </Button>
              </>
            ) : null}
          </>
        )}
        {watchlistActionErr != null ? (
          <p className="text-sm text-(--tgui--destructive_text_color)">{watchlistActionErr}</p>
        ) : null}
      </>
    ) : null

  return (
    <>
      <TitleCommunityDetailLayout
      headerLabel="Тема в каталоге"
      loading={loading}
      error={error}
      sectionHeader={film?.title}
      heroVariant="film"
      title={film?.title ?? ''}
      posterUrl={film?.poster_url}
      posterAlt={film?.title}
      titleMeta={titleMeta}
      shortDescription={film?.short_description}
      longDescription={film?.description}
      descExpanded={descExpanded}
      onToggleDescription={() => setDescExpanded((v) => !v)}
      overlapBanner={
        auth.kind === 'ready' && film != null ? (
          <WatchlistOverlapAnchorBanner
            anchor={filmOverlapAnchor}
            enabled={!hasMyRatedCard}
            inViewerWatchlist={inWatchlist}
          />
        ) : null
      }
      watchlistActions={watchlistActions}
      followingRatings={auth.kind === 'ready' ? <FollowingRatingsPanel rows={followingRatings} /> : null}
      communityRatings={
        <CommunityRatingsList
          items={community}
          loading={communityLoading}
          error={communityErr}
          nextCursor={communityNext}
          moreBusy={communityMoreBusy}
          viewerId={viewerId}
          tasteQuizKnowledgeByAuthor={tasteQuizKnowledgeByAuthor}
          streakByUserId={streakByUserId}
          watchingByUserId={watchingByUserId}
          followingUserIds={followingUserIds}
          onLoadMore={() => void loadMoreCommunity()}
        />
      }
      ready={film != null}
    />
    </>
  )
}
