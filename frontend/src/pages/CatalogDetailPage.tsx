import { Button, Section, Title } from '@telegram-apps/telegram-ui'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'

import { getCatalogCommunityCardsPage, getCatalogItemById } from '../api/cardApi'
import type { CatalogItemDetail, CommunityCardItem } from '../api/catalogTypes'
import { ApiError, formatApiDetail } from '../api/client'
import { CommunityRatingsList } from '../components/catalog/CommunityRatingsList'
import { WatchlistOverlapAnchorBanner } from '../components/watchlist/WatchlistOverlapSection'
import { useAuthStatus } from '../auth/useAuthStatus'
import { useTasteQuizKnowledgeOfUsers } from '../hooks/useTasteQuizKnowledgeOfUsers'
import { useRatingStreaksOfUsers } from '../hooks/useRatingStreaksOfUsers'
import { readMyProfileBundleCache } from '../lib/myProfileBundleCache'
import { resolveApiMediaUrl } from '../lib/resolveApiMediaUrl'

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
  const [viewerId] = useState<string | null>(
    () => readMyProfileBundleCache()?.profile.id ?? null,
  )

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
  const longDescription = item?.description?.trim() ?? ''
  const headerLabel = item?.kind === 'game' ? 'Игра в каталоге' : 'Тема в каталоге'

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
        <span className="truncate text-sm font-medium text-(--tgui--hint_color)">{headerLabel}</span>
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
        {!loading && error == null && item != null ? (
          <>
            <WatchlistOverlapAnchorBanner anchor={catalogOverlapAnchor} />

            <Section>
              <div className="flex flex-col gap-4 px-3 py-3">
                {item.poster_url != null ? (
                  <img
                    src={resolveApiMediaUrl(item.poster_url) ?? item.poster_url}
                    alt=""
                    className="mx-auto max-h-72 w-auto max-w-full rounded-xl object-cover"
                  />
                ) : null}
                <div>
                  <Title level="2" weight="2">
                    {item.title}
                    {item.year != null ? ` (${item.year})` : ''}
                  </Title>
                  {item.short_description?.trim() ? (
                    <p className="mt-2 text-[14px] leading-relaxed text-(--tgui--hint_color)">
                      {item.short_description}
                    </p>
                  ) : null}
                  {longDescription !== '' ? (
                    <div className="mt-2">
                      <p
                        className={
                          descExpanded
                            ? 'text-[14px] leading-relaxed text-(--tgui--text_color)'
                            : 'line-clamp-4 text-[14px] leading-relaxed text-(--tgui--text_color)'
                        }
                      >
                        {longDescription}
                      </p>
                      {longDescription.length > 200 ? (
                        <button
                          type="button"
                          className="mt-1 text-xs font-medium text-(--tgui--link_color)"
                          onClick={() => setDescExpanded((v) => !v)}
                        >
                          {descExpanded ? 'Свернуть' : 'Показать полностью'}
                        </button>
                      ) : null}
                    </div>
                  ) : null}
                </div>

                {auth.kind === 'ready' ? (
                  <div className="flex flex-col gap-2">
                    {hasMyRatedCard ? (
                      <>
                        <Link
                          to={`/cards/${encodeURIComponent(String(item.my_card_id))}`}
                          className="no-underline"
                        >
                          <Button stretched>Открыть мою карточку</Button>
                        </Link>
                        <Link
                          to={`/cards/${encodeURIComponent(String(item.my_card_id))}/edit`}
                          className="no-underline"
                        >
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
                        <Link
                          to={`/watchlist/new?catalogItemId=${encodeURIComponent(String(item.catalog_item_id))}`}
                          className="no-underline"
                        >
                          <Button mode="gray" stretched>
                            В список «Позже»
                          </Button>
                        </Link>
                      </>
                    )}
                  </div>
                ) : null}
              </div>
            </Section>

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
