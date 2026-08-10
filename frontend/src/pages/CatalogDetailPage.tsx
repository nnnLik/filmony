import { Button } from '@telegram-apps/telegram-ui'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'

import { getCatalogCommunityCardsPage, getCatalogItemById, getFollowingRatingsForCatalogItem } from '../api/cardApi'
import type { CatalogItemDetail, CommunityCardItem } from '../api/catalogTypes'
import { ApiError, formatApiDetail } from '../api/client'
import {
  deleteMyWatchlistEntry,
  deleteMyWatchlistFilm,
  getMyPlannedCard,
  getMyWatchlistPresence,
  getUserWatchlist,
} from '../api/profileApi'
import { CommunityRatingsList } from '../components/catalog/CommunityRatingsList'
import { TitleCommunityDetailLayout } from '../components/catalog/TitleCommunityDetailLayout'
import { PageErrorState } from '../components/ui/PageErrorState'
import { PageLoadingState } from '../components/ui/PageLoadingState'
import { FollowingRatingsPanel } from '../components/social/FollowingRatingsPanel'
import {
  buildFollowingRatingDisplayRows,
  type FollowingRatingRow,
} from '../lib/followingRatingsDisplay'
import { WatchlistOverlapAnchorBanner } from '../components/watchlist/WatchlistOverlapSection'
import { useAuthStatus } from '../auth/useAuthStatus'
import { useTasteQuizKnowledgeOfUsers } from '../hooks/useTasteQuizKnowledgeOfUsers'
import { useRatingStreaksOfUsers } from '../hooks/useRatingStreaksOfUsers'
import { readMyProfileBundleCache, clearMyProfileBundleCache } from '../lib/myProfileBundleCache'

function catalogWatchlistCardId(item: CatalogItemDetail): string {
  return item.provider === 'kinopoisk'
    ? `kp:${item.external_id}`
    : `${item.provider}:${item.external_id}`
}

export function CatalogDetailPage() {
  const auth = useAuthStatus()
  const navigate = useNavigate()
  const { catalogItemId: catalogItemIdRaw } = useParams<{ catalogItemId: string }>()
  const parsedId = Number(catalogItemIdRaw)
  const catalogItemId = Number.isInteger(parsedId) && parsedId >= 1 ? parsedId : 0

  const [item, setItem] = useState<CatalogItemDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [descExpanded, setDescExpanded] = useState(false)

  const [community, setCommunity] = useState<CommunityCardItem[]>([])
  const [communityNext, setCommunityNext] = useState<string | null>(null)
  const [communityLoading, setCommunityLoading] = useState(false)
  const [communityErr, setCommunityErr] = useState<string | null>(null)
  const [communityMoreBusy, setCommunityMoreBusy] = useState(false)
  const [followingRatings, setFollowingRatings] = useState<FollowingRatingRow[] | null>(null)
  const [inWatchlist, setInWatchlist] = useState<boolean | null>(null)
  const [plannedUserCardId, setPlannedUserCardId] = useState<number | null>(null)
  const [removeBusy, setRemoveBusy] = useState(false)
  const [watchlistActionErr, setWatchlistActionErr] = useState<string | null>(null)
  const [viewerId] = useState<string | null>(() => readMyProfileBundleCache()?.profile.id ?? null)

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

  useEffect(() => {
    let alive = true
    void (async () => {
      await Promise.resolve()
      if (!alive) return
      if (catalogItemId < 1) {
        setError('Некорректный id в каталоге')
        setLoading(false)
        setItem(null)
        return
      }
      setLoading(true)
      setError(null)
      try {
        const detail = await getCatalogItemById(catalogItemId)
        if (!alive) return
        setItem(detail)
      } catch (e) {
        if (!alive) return
        if (e instanceof ApiError && e.status === 404) {
          setError('Запись в каталоге не найдена.')
        } else if (e instanceof ApiError) {
          setError(formatApiDetail(e.detail))
        } else {
          setError('Не удалось загрузить запись каталога')
        }
        setItem(null)
      } finally {
        if (alive) setLoading(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [catalogItemId])

  useEffect(() => {
    if (item == null || catalogItemId < 1) {
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
      void getCatalogCommunityCardsPage(catalogItemId, { limit: 25 })
        .then((page) => {
          if (!alive) return
          setCommunity(page.items)
          setCommunityNext(page.next_cursor)
        })
        .catch((e: unknown) => {
          if (!alive) return
          setCommunity([])
          setCommunityNext(null)
          setCommunityErr(
            e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось загрузить оценки',
          )
        })
        .finally(() => {
          if (alive) setCommunityLoading(false)
        })
    })
    return () => {
      alive = false
    }
  }, [item, catalogItemId])

  useEffect(() => {
    if (auth.kind !== 'ready' || catalogItemId < 1) {
      queueMicrotask(() => setFollowingRatings(null))
      return
    }
    let alive = true
    queueMicrotask(() => {
      if (alive) setFollowingRatings(null)
    })
    void getFollowingRatingsForCatalogItem(catalogItemId)
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
  }, [auth.kind, catalogItemId])

  useEffect(() => {
    let alive = true
    void (async () => {
      if (auth.kind !== 'ready' || item == null) {
        queueMicrotask(() => {
          if (auth.kind !== 'ready') setInWatchlist(null)
        })
        return
      }
      try {
        const cardId = catalogWatchlistCardId(item)
        const m = await getMyWatchlistPresence(cardId)
        if (!alive) return
        setInWatchlist(m.in_watchlist)
        if (m.in_watchlist) {
          try {
            const planned = await getMyPlannedCard(
              item.film_id != null && item.film_id > 0
                ? { film_id: item.film_id }
                : { catalog_item_id: item.catalog_item_id },
            )
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
  }, [auth.kind, item])

  const onAddToWatchlist = useCallback(() => {
    if (item == null) return
    void navigate(`/watchlist/new?catalogItemId=${encodeURIComponent(String(item.catalog_item_id))}`)
  }, [item, navigate])

  const onRemoveFromWatchlist = useCallback(async () => {
    if (item == null) return
    setRemoveBusy(true)
    setWatchlistActionErr(null)
    try {
      if (item.film_id != null && item.film_id > 0) {
        await deleteMyWatchlistFilm(item.film_id)
      } else if (viewerId != null) {
        const page = await getUserWatchlist(viewerId, { limit: 50 })
        const cardId = catalogWatchlistCardId(item)
        const entry = page.items.find((row) => row.card_id === cardId)
        if (entry == null) {
          throw new Error('watchlist entry not found')
        }
        await deleteMyWatchlistEntry(entry.entry_id)
      }
      setInWatchlist(false)
      setPlannedUserCardId(null)
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
  }, [item, viewerId])

  const loadMoreCommunity = useCallback(async () => {
    if (catalogItemId < 1 || communityNext == null) return
    setCommunityMoreBusy(true)
    try {
      const page = await getCatalogCommunityCardsPage(catalogItemId, {
        cursor: communityNext,
        limit: 25,
      })
      setCommunity((prev) => [...prev, ...page.items])
      setCommunityNext(page.next_cursor)
    } catch (e) {
      setCommunityErr(
        e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось подгрузить оценки',
      )
    } finally {
      setCommunityMoreBusy(false)
    }
  }, [catalogItemId, communityNext])

  const catalogOverlapAnchor = useMemo(
    () =>
      item != null
        ? {
            card_id: null,
            film_id: item.film_id,
            catalog_item_id: item.catalog_item_id,
          }
        : null,
    [item],
  )

  const hasMyRatedCard = item != null && item.my_card_id != null && item.my_card_id > 0
  const headerLabel = item?.kind === 'game' ? 'Игра в каталоге' : 'Тема в каталоге'
  const displayTitle =
    item != null ? `${item.title}${item.year != null ? ` (${item.year})` : ''}` : ''

  if (auth.kind === 'loading' || auth.kind === 'unauthenticated') {
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

  const watchlistActions =
    auth.kind === 'ready' && item != null ? (
      <>
        {hasMyRatedCard ? (
          <>
            <Link to={`/cards/${encodeURIComponent(String(item.my_card_id))}`} className="no-underline">
              <Button stretched>Открыть мою карточку</Button>
            </Link>
            <Link to={`/cards/${encodeURIComponent(String(item.my_card_id))}/edit`} className="no-underline">
              <Button mode="gray" stretched>
                Редактировать оценку
              </Button>
            </Link>
          </>
        ) : (
          <>
            <Link
              to={`/cards/new?catalogItemId=${encodeURIComponent(String(item.catalog_item_id))}`}
              className="no-underline"
            >
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
    <TitleCommunityDetailLayout
      headerLabel={headerLabel}
      loading={loading}
      error={error}
      heroVariant="catalog"
      title={displayTitle}
      posterUrl={item?.poster_url}
      shortDescription={item?.short_description}
      longDescription={item?.description}
      descExpanded={descExpanded}
      onToggleDescription={() => setDescExpanded((v) => !v)}
      overlapPlacement="above-section"
      overlapBanner={
        item != null ? (
          <WatchlistOverlapAnchorBanner anchor={catalogOverlapAnchor} inViewerWatchlist={inWatchlist} />
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
          followingUserIds={followingUserIds}
          onLoadMore={() => void loadMoreCommunity()}
        />
      }
      ready={item != null}
    />
  )
}
