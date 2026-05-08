import { Avatar, Button, Section, Title } from '@telegram-apps/telegram-ui'
import { useEffect, useMemo, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'

import { ApiError, formatApiDetail } from '../api/client'
import {
  getMyProfile,
  getPublicProfileById,
  getUserSubscriptions,
  subscribeToUser,
  unsubscribeFromUser,
} from '../api/profileApi'
import type {
  MyProfile,
  PublicProfile,
  SubscriptionListItem,
  SubscriptionListType,
} from '../api/profileTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { displayNameFromProfile, profileInitials } from '../lib/profileDisplay'

type SubscriptionsTab = 'following' | 'followers'

function toPublicShapeFromMe(me: MyProfile): PublicProfile {
  return {
    id: me.id,
    profile_slug: me.profile_slug,
    username: me.username,
    first_name: me.first_name,
    last_name: me.last_name,
    photo_url: me.photo_url,
    display_name: me.display_name,
    bio: me.bio,
    cards_count: me.cards_count,
    favorites_count: me.favorites_count,
    watchlist_count: me.watchlist_count,
    friends_count: me.friends_count,
    followers_count: me.followers_count,
    following_count: me.following_count,
  }
}

function asCount(value: number | undefined): string {
  return typeof value === 'number' ? String(value) : '0'
}

function tabFromSearch(searchParams: URLSearchParams): SubscriptionsTab {
  const tab = searchParams.get('tab')
  return tab === 'followers' ? 'followers' : 'following'
}

const loadMyProfile: () => Promise<MyProfile> = getMyProfile
const loadPublicProfileById: (userId: string) => Promise<PublicProfile> = getPublicProfileById
const loadUserSubscriptions: (
  userId: string,
  type: SubscriptionListType,
) => Promise<{ items: SubscriptionListItem[] }> = getUserSubscriptions
const followUser: (userId: string) => Promise<void> = subscribeToUser
const unfollowUser: (userId: string) => Promise<void> = unsubscribeFromUser

export function SubscriptionsPage() {
  const auth = useAuthStatus()
  const { userId } = useParams<{ userId?: string }>()
  const resolvedUserId = useMemo(() => decodeURIComponent(userId ?? ''), [userId])
  const [searchParams, setSearchParams] = useSearchParams()

  const tab = tabFromSearch(searchParams)
  const [targetProfile, setTargetProfile] = useState<PublicProfile | null>(null)
  const [myProfile, setMyProfile] = useState<PublicProfile | null>(null)
  const [items, setItems] = useState<SubscriptionListItem[]>([])
  const [myFollowingIds, setMyFollowingIds] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(false)
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (auth.kind !== 'ready') {
      return
    }
    if (userId != null && resolvedUserId === '') {
      return
    }
    let alive = true
    void (async () => {
      setLoading(true)
      setError(null)
      try {
        const me = await loadMyProfile()
        if (!alive) {
          return
        }
        const mePublic = toPublicShapeFromMe(me)
        setMyProfile(mePublic)

        const target = userId
          ? await loadPublicProfileById(resolvedUserId)
          : mePublic
        if (!alive) {
          return
        }
        setTargetProfile(target)

        const followingList = await loadUserSubscriptions(me.id, 'following')
        if (!alive) {
          return
        }
        setMyFollowingIds(new Set(followingList.items.map((x) => x.id)))
      } catch (e) {
        if (!alive) {
          return
        }
        if (e instanceof ApiError) {
          setError(formatApiDetail(e.detail))
        } else {
          setError(e instanceof Error ? e.message : 'Ошибка загрузки')
        }
      } finally {
        if (alive) {
          setLoading(false)
        }
      }
    })()
    return () => {
      alive = false
    }
  }, [auth.kind, userId, resolvedUserId])

  useEffect(() => {
    if (auth.kind !== 'ready' || targetProfile == null) {
      return
    }
    let alive = true
    void (async () => {
      setLoading(true)
      setError(null)
      try {
        const listType: SubscriptionListType = tab
        const list = await loadUserSubscriptions(targetProfile.id, listType)
        if (!alive) {
          return
        }
        setItems(list.items)
      } catch (e) {
        if (!alive) {
          return
        }
        if (e instanceof ApiError) {
          setError(formatApiDetail(e.detail))
        } else {
          setError(e instanceof Error ? e.message : 'Ошибка списка')
        }
      } finally {
        if (alive) {
          setLoading(false)
        }
      }
    })()
    return () => {
      alive = false
    }
  }, [auth.kind, targetProfile, tab])

  const backTo = userId ? `/u/${encodeURIComponent(resolvedUserId)}` : '/profile'

  function switchTab(nextTab: SubscriptionsTab) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      next.set('tab', nextTab)
      return next
    })
  }

  async function toggleFollow(userId: string) {
    if (myProfile == null) {
      return
    }
    setActionLoadingId(userId)
    const currentlyFollowing = myFollowingIds.has(userId)
    try {
      if (currentlyFollowing) {
        await unfollowUser(userId)
      } else {
        await followUser(userId)
      }
      setMyFollowingIds((prev) => {
        const next = new Set(prev)
        if (currentlyFollowing) {
          next.delete(userId)
        } else {
          next.add(userId)
        }
        return next
      })
    } catch (e) {
      if (e instanceof ApiError) {
        setError(formatApiDetail(e.detail))
      } else {
        setError(e instanceof Error ? e.message : 'Не удалось обновить подписку')
      }
    } finally {
      setActionLoadingId(null)
    }
  }

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
          Откройте приложение в Telegram, чтобы увидеть подписки.
        </p>
        <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to="/">
          На главную
        </Link>
      </div>
    )
  }

  if (error != null) {
    return (
      <div className="mx-auto max-w-md px-4 py-12">
        <p className="filmony-text-panel text-sm text-(--tgui--destructive_text_color)">{error}</p>
        <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to={backTo}>
          Назад
        </Link>
      </div>
    )
  }

  if (userId != null && resolvedUserId === '') {
    return (
      <div className="mx-auto max-w-md px-4 py-12">
        <p className="filmony-text-panel text-sm text-(--tgui--destructive_text_color)">Не указан пользователь.</p>
        <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to={backTo}>
          Назад
        </Link>
      </div>
    )
  }

  if (targetProfile == null || myProfile == null) {
    return (
      <div className="px-4 py-16 text-center text-sm text-(--tgui--hint_color)">
        <p className="filmony-text-panel inline-block">Загрузка…</p>
      </div>
    )
  }

  const shownName = displayNameFromProfile(targetProfile)

  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-20 flex items-center gap-2 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] px-2 py-2 backdrop-blur-md">
        <Link
          className="flex min-h-10 min-w-10 items-center justify-center rounded-xl text-lg text-(--tgui--link_color) no-underline"
          to={backTo}
          aria-label="Назад"
        >
          ←
        </Link>
        <h1 className="text-base font-semibold tracking-tight text-(--tgui--text_color)">Подписки</h1>
      </header>

      <main className="mx-auto max-w-md px-4 py-5">
        <div className="mb-4 flex flex-col items-center text-center">
          <Avatar
            src={targetProfile.photo_url ?? undefined}
            acronym={profileInitials(targetProfile)}
            size={72}
          />
          <Title className="mt-3" level="2" weight="2">
            {shownName}
          </Title>
          <p className="mt-1 font-mono text-xs text-(--tgui--hint_color)">@{targetProfile.profile_slug}</p>
        </div>

        <div className="mb-4 flex gap-1 rounded-full bg-(--tgui--secondary_bg_color) p-1">
          <button
            type="button"
            className={`flex flex-1 items-center justify-center rounded-full py-2.5 text-sm font-medium transition-all ${
              tab === 'following'
                ? 'bg-(--tgui--bg_color) text-(--tgui--text_color) shadow-sm'
                : 'text-(--tgui--hint_color)'
            }`}
            onClick={() => switchTab('following')}
          >
            Подписки ({asCount(targetProfile.following_count)})
          </button>
          <button
            type="button"
            className={`flex flex-1 items-center justify-center rounded-full py-2.5 text-sm font-medium transition-all ${
              tab === 'followers'
                ? 'bg-(--tgui--bg_color) text-(--tgui--text_color) shadow-sm'
                : 'text-(--tgui--hint_color)'
            }`}
            onClick={() => switchTab('followers')}
          >
            Подписчики ({asCount(targetProfile.followers_count)})
          </button>
        </div>

        <Section>
          {loading ? (
            <p className="filmony-text-panel mx-4 my-4 text-center text-sm text-(--tgui--hint_color)">Загрузка…</p>
          ) : null}
          {!loading && items.length === 0 ? (
            <p className="filmony-text-panel mx-4 my-4 text-center text-sm text-(--tgui--hint_color)">
              Пока список пуст.
            </p>
          ) : null}
          {!loading && items.length > 0 ? (
            <div className="space-y-2 px-1 pb-2">
              {items.map((item) => {
                const following = myFollowingIds.has(item.id)
                const selfRow = item.id === myProfile.id
                return (
                  <div
                    key={`${item.relation_type}-${item.id}`}
                    className="flex items-center gap-3 rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-3 py-2"
                  >
                    <Avatar src={item.photo_url ?? undefined} acronym={profileInitials(item)} size={40} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-(--tgui--text_color)">
                        {displayNameFromProfile(item)}
                      </p>
                      <p className="truncate text-xs text-(--tgui--hint_color)">@{item.profile_slug}</p>
                    </div>
                    {selfRow ? null : (
                      <Button
                        mode={following ? 'gray' : 'filled'}
                        size="s"
                        disabled={actionLoadingId === item.id}
                        onClick={() => void toggleFollow(item.id)}
                      >
                        {actionLoadingId === item.id
                          ? '...'
                          : following
                            ? 'Отписаться'
                            : 'Подписаться'}
                      </Button>
                    )}
                  </div>
                )
              })}
            </div>
          ) : null}
        </Section>
      </main>
    </div>
  )
}
