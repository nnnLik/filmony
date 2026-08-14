import { Avatar, Button } from '@telegram-apps/telegram-ui'
import { useQuery } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router'

import { ApiError, formatApiDetail } from '../../api/client'
import { getEveningForTwoPick } from '../../api/eveningForTwoApi'
import { getMyProfile, getUserSubscriptions } from '../../api/profileApi'
import type { EveningForTwoPick, SubscriptionListItem } from '../../api/profileTypes'
import { filterMutualSubscriptions } from '../../lib/mutualSubscriptionFilter'
import { displayNameFromProfile, profileInitials } from '../../lib/profileDisplay'
import { onWatchCtaClick } from '../../lib/openFilmWatchInBrowser'

function toPublicFromSubscription(row: SubscriptionListItem) {
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
    favorites_count: 0,
    watchlist_count: 0,
    friends_count: 0,
    followers_count: 0,
    following_count: 0,
  }
}

function partnerLabel(pick: EveningForTwoPick): string {
  if (pick.partner.display_name?.trim()) {
    return pick.partner.display_name.trim()
  }
  if (pick.partner.slug?.trim()) {
    return `@${pick.partner.slug.trim()}`
  }
  return 'другом'
}

export type EveningForTwoSectionProps = {
  enabled?: boolean
}

export function EveningForTwoSection({ enabled = true }: EveningForTwoSectionProps) {
  const [friends, setFriends] = useState<SubscriptionListItem[]>([])
  const [friendsLoading, setFriendsLoading] = useState(false)
  const [selectedPartnerId, setSelectedPartnerId] = useState<string | null>(null)
  const [pickAttempt, setPickAttempt] = useState(0)

  useEffect(() => {
    if (!enabled) {
      return undefined
    }
    let alive = true
    queueMicrotask(() => {
      if (alive) {
        setFriendsLoading(true)
      }
    })
    void (async () => {
      try {
        const me = await getMyProfile()
        const subs = await getUserSubscriptions(me.id, 'both')
        if (!alive) return
        const mutual = filterMutualSubscriptions(subs.items)
        setFriends(mutual)
        if (mutual.length === 1) {
          setSelectedPartnerId(mutual[0].id)
        }
      } catch {
        if (!alive) return
        setFriends([])
      } finally {
        if (alive) setFriendsLoading(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [enabled])

  const pickQuery = useQuery({
    queryKey: ['eveningForTwo', selectedPartnerId, pickAttempt],
    queryFn: () => getEveningForTwoPick(selectedPartnerId as string),
    enabled: enabled && pickAttempt > 0 && selectedPartnerId != null,
    retry: false,
    gcTime: 10 * 60_000,
  })

  const pickError = useMemo(() => {
    if (pickAttempt === 0 || !pickQuery.isError) {
      return null
    }
    const error = pickQuery.error
    if (error instanceof ApiError) {
      if (error.status === 404) {
        return 'Нет подходящих фильмов — добавьте общие тайтлы в «Позже» или выберите другого друга.'
      }
      if (error.status === 403) {
        return 'Нужна взаимная подписка с выбранным другом.'
      }
      return formatApiDetail(error.detail)
    }
    return 'Не удалось подобрать фильм'
  }, [pickAttempt, pickQuery.error, pickQuery.isError])

  if (!enabled) {
    return null
  }

  return (
    <div className="mb-6 border-b border-[color-mix(in_srgb,var(--tgui--divider_color)_85%,transparent)] pb-5">
      <div className="mb-3 px-1">
        <p className="text-sm font-semibold text-(--tgui--text_color)">Вечер на двоих</p>
        <p className="mt-0.5 text-xs text-(--tgui--hint_color)">
          Подберём фильм из общего «Позже», который вы ещё не оценивали
        </p>
      </div>

      {friendsLoading ? (
        <p className="px-1 text-xs text-(--tgui--hint_color)">Загружаем друзей…</p>
      ) : null}

      {!friendsLoading && friends.length === 0 ? (
        <p className="px-1 text-xs text-(--tgui--hint_color)">
          Нужны взаимные подписки — тогда можно выбрать друга и подобрать фильм на вечер.
        </p>
      ) : null}

      {!friendsLoading && friends.length > 0 ? (
        <div className="space-y-3 px-1">
          <ul className="flex flex-col gap-2">
            {friends.map((row) => {
              const pub = toPublicFromSubscription(row)
              const name = displayNameFromProfile(pub)
              const selected = selectedPartnerId === row.id
              return (
                <li key={row.id}>
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedPartnerId(row.id)
                      setPickAttempt(0)
                    }}
                    className={`flex w-full items-center gap-3 rounded-2xl border px-3 py-2.5 text-left transition ${
                      selected
                        ? 'border-(--tgui--link_color) bg-[color-mix(in_srgb,var(--tgui--link_color)_12%,var(--tgui--secondary_bg_color))]'
                        : 'border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color)'
                    }`}
                  >
                    <span className="flex size-5 shrink-0 items-center justify-center rounded-full border border-(--tgui--divider_color) bg-(--tgui--bg_color)">
                      {selected ? <span className="text-xs text-(--tgui--link_color)">✓</span> : null}
                    </span>
                    <Avatar src={row.photo_url ?? undefined} acronym={profileInitials(pub)} size={36} />
                    <span className="min-w-0 flex-1 truncate text-sm font-medium">{name}</span>
                  </button>
                </li>
              )
            })}
          </ul>

          <Button
            size="s"
            stretched
            disabled={selectedPartnerId == null || pickQuery.isFetching}
            onClick={() => {
              setPickAttempt((attempt) => attempt + 1)
            }}
          >
            {pickQuery.isFetching ? 'Подбираем…' : 'Вечер на двоих'}
          </Button>
        </div>
      ) : null}

      {pickError != null ? (
        <p className="mt-2 px-1 text-xs text-(--tgui--destructive_text_color)">{pickError}</p>
      ) : null}

      {pickAttempt > 0 && pickQuery.data != null && !pickQuery.isFetching ? (
        <div className="mt-4 overflow-hidden rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color)">
          <div className="flex gap-3 p-3">
            <div className="h-24 w-16 shrink-0 overflow-hidden rounded-lg bg-(--tgui--bg_color)">
              {pickQuery.data.poster_url ? (
                <img
                  src={pickQuery.data.poster_url}
                  alt={pickQuery.data.title}
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="flex h-full items-center justify-center px-1 text-center text-[10px] text-(--tgui--hint_color)">
                  Нет постера
                </div>
              )}
            </div>
            <div className="min-w-0 flex-1">
              <p className="line-clamp-2 text-sm font-semibold text-(--tgui--text_color)">
                {pickQuery.data.title}
              </p>
              <p className="mt-1 text-xs text-(--tgui--hint_color)">
                С {partnerLabel(pickQuery.data)} из общего «Позже»
              </p>
              <Link
                to={`/films/${encodeURIComponent(String(pickQuery.data.film_id))}/watch`}
                className="mt-3 block no-underline"
                onClick={(event) => {
                  void onWatchCtaClick(event, pickQuery.data.film_id)
                }}
              >
                <Button size="s" stretched>
                  Смотреть
                </Button>
              </Link>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
