import { Avatar, Button } from '@telegram-apps/telegram-ui'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Users } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router'

import { ApiError, formatApiDetail } from '../../api/client'
import { patchMyWatchlistEntry } from '../../api/profileApi'
import type { CardCompany, WatchlistOverlapItem } from '../../api/profileTypes'
import { getMyWatchlistOverlaps } from '../../api/watchlistApi'
import { clearMyProfileBundleCache } from '../../lib/myProfileBundleCache'
import {
  buildWatchlistNewHref,
  findWatchlistOverlapForAnchor,
  mergedOverlapWatchWithUserIds,
  overlapPartnersToInvite,
  type WatchlistOverlapAnchor,
} from '../../lib/watchlistOverlapUtils'
import type { WatchlistOverlapPartner } from '../../api/profileTypes'
import { profileInitials } from '../../lib/profileDisplay'
import { safeHapticSuccess } from '../../lib/safeHaptic'

import { WatchTogetherConfirmSheet } from './WatchTogetherConfirmSheet'

function partnerDisplayName(partner: WatchlistOverlapPartner): string {
  if (partner.display_name?.trim()) {
    return partner.display_name.trim()
  }
  if (partner.slug?.trim()) {
    return `@${partner.slug.trim()}`
  }
  return 'Пользователь'
}

function partnerInitials(partner: WatchlistOverlapPartner): string {
  return profileInitials({
    display_name: partner.display_name,
    first_name: null,
    username: partner.slug,
  })
}

type ConfirmState = {
  item: WatchlistOverlapItem
  partners: WatchlistOverlapPartner[]
}

async function inviteOverlapPartners(item: WatchlistOverlapItem, partners: WatchlistOverlapPartner[]): Promise<void> {
  const company: CardCompany = item.company === 'alone' ? 'friends' : item.company
  await patchMyWatchlistEntry(item.entry_id, {
    company,
    watch_note: item.watch_note,
    watch_with_user_ids: mergedOverlapWatchWithUserIds(item, partners),
  })
}

export type WatchlistOverlapSectionProps = {
  enabled?: boolean
}

function OverlapCard({
  item,
  onInvite,
  allInvited,
}: {
  item: WatchlistOverlapItem
  onInvite: () => void
  allInvited: boolean
}) {
  const partnerPreview = item.partners.slice(0, 3)
  const extraCount = Math.max(0, item.partners.length - partnerPreview.length)
  const pendingCount = overlapPartnersToInvite(item).length

  return (
    <div className="w-34 shrink-0 overflow-hidden rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color)">
      <div className="relative aspect-2/3 w-full">
        {item.poster_url ? (
          <img src={item.poster_url} alt={item.title} className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full min-h-26 items-center justify-center px-1 text-center text-[10px] text-(--tgui--hint_color)">
            Нет постера
          </div>
        )}
        <span className="absolute bottom-1.5 left-1.5 flex items-center gap-0.5 rounded-md bg-[color-mix(in_srgb,var(--tgui--bg_color)_82%,transparent)] px-1.5 py-0.5 text-[10px] font-medium text-(--tgui--text_color) shadow-sm backdrop-blur-sm">
          <Users className="block" size={11} strokeWidth={2} aria-hidden />
          {item.partners.length}
        </span>
      </div>
      <div className="space-y-2 p-2">
        <p className="line-clamp-2 min-h-10 text-[11px] font-medium leading-snug text-(--tgui--text_color)">
          {item.title}
        </p>
        {partnerPreview.length > 0 ? (
          <div className="flex items-center gap-1">
            {partnerPreview.map((partner) => (
              <Avatar
                key={partner.user_id}
                src={partner.avatar_url ?? undefined}
                acronym={partnerInitials(partner)}
                size={24}
              />
            ))}
            {extraCount > 0 ? (
              <span className="text-[10px] font-medium text-(--tgui--hint_color)">+{extraCount}</span>
            ) : null}
          </div>
        ) : null}
        <Button size="s" stretched disabled={allInvited} onClick={onInvite}>
          {allInvited ? 'Уже вместе' : pendingCount === 1 ? 'Пригласить' : 'Пригласить всех'}
        </Button>
      </div>
    </div>
  )
}

export function WatchlistOverlapSection({ enabled = true }: WatchlistOverlapSectionProps) {
  const queryClient = useQueryClient()
  const [confirm, setConfirm] = useState<ConfirmState | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const overlapsQuery = useQuery({
    queryKey: ['watchlistOverlaps'],
    queryFn: () => getMyWatchlistOverlaps({ limit: 20 }),
    enabled,
    staleTime: 60_000,
    gcTime: 10 * 60_000,
  })

  const inviteMutation = useMutation({
    mutationFn: async (state: ConfirmState) => inviteOverlapPartners(state.item, state.partners),
    onSuccess: async () => {
      safeHapticSuccess()
      setConfirm(null)
      setActionError(null)
      clearMyProfileBundleCache()
      await queryClient.invalidateQueries({ queryKey: ['watchlistOverlaps'] })
      await queryClient.invalidateQueries({ queryKey: ['userWatchlist'] })
    },
    onError: (error: unknown) => {
      if (error instanceof ApiError) {
        setActionError(formatApiDetail(error.detail))
      } else {
        setActionError('Не удалось отправить приглашение')
      }
    },
  })

  const items = overlapsQuery.data?.items ?? []
  if (!enabled || overlapsQuery.isLoading || items.length === 0) {
    return null
  }

  return (
    <>
      <div className="mb-6 border-b border-[color-mix(in_srgb,var(--tgui--divider_color)_85%,transparent)] pb-5">
        <div className="mb-1 px-1">
          <p className="text-sm font-semibold text-(--tgui--text_color)">С друзьями в «Позже»</p>
          <p className="mt-0.5 text-xs text-(--tgui--hint_color)">
            Эти фильмы уже у вас в списке — можно пригласить друзей смотреть вместе
          </p>
        </div>
        {actionError != null ? (
          <p className="mb-2 px-1 text-xs text-(--tgui--destructive_text_color)">{actionError}</p>
        ) : null}
        <div className="mt-3 flex gap-2.5 overflow-x-auto overflow-y-hidden pb-1 pl-1 pr-1 pt-0.5 [-ms-overflow-style:none] scrollbar-none [&::-webkit-scrollbar]:hidden">
          {items.map((item) => {
            const pending = overlapPartnersToInvite(item)
            return (
              <OverlapCard
                key={item.card_id}
                item={item}
                allInvited={pending.length === 0}
                onInvite={() => {
                  if (pending.length === 0) return
                  setActionError(null)
                  setConfirm({ item, partners: pending })
                }}
              />
            )
          })}
        </div>
      </div>

      {confirm != null ? (
        <WatchTogetherConfirmSheet
          open
          mode="invite"
          title={confirm.item.title}
          posterUrl={confirm.item.poster_url}
          partners={confirm.partners}
          busy={inviteMutation.isPending}
          onClose={() => {
            if (!inviteMutation.isPending) {
              setConfirm(null)
            }
          }}
          onConfirm={() => {
            inviteMutation.mutate(confirm)
          }}
        />
      ) : null}
    </>
  )
}

export type WatchlistOverlapAnchorBannerProps = {
  anchor: WatchlistOverlapAnchor | null
  enabled?: boolean
  inViewerWatchlist?: boolean | null
  onWatchTogether?: () => void
}

export function WatchlistOverlapAnchorBanner({
  anchor,
  enabled = true,
  inViewerWatchlist = null,
  onWatchTogether,
}: WatchlistOverlapAnchorBannerProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [confirm, setConfirm] = useState<ConfirmState | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const overlapsQuery = useQuery({
    queryKey: ['watchlistOverlaps'],
    queryFn: () => getMyWatchlistOverlaps({ limit: 50 }),
    enabled: enabled && anchor != null,
    staleTime: 60_000,
    gcTime: 10 * 60_000,
  })

  const inviteMutation = useMutation({
    mutationFn: async (state: ConfirmState) => inviteOverlapPartners(state.item, state.partners),
    onSuccess: async () => {
      safeHapticSuccess()
      setConfirm(null)
      setActionError(null)
      clearMyProfileBundleCache()
      await queryClient.invalidateQueries({ queryKey: ['watchlistOverlaps'] })
      await queryClient.invalidateQueries({ queryKey: ['userWatchlist'] })
    },
    onError: (error: unknown) => {
      if (error instanceof ApiError) {
        setActionError(formatApiDetail(error.detail))
      } else {
        setActionError('Не удалось отправить приглашение')
      }
    },
  })

  const overlap = useMemo(() => {
    if (anchor == null || overlapsQuery.data == null) {
      return null
    }
    return findWatchlistOverlapForAnchor(overlapsQuery.data.items, anchor)
  }, [anchor, overlapsQuery.data])

  const pendingPartners = overlap != null ? overlapPartnersToInvite(overlap) : []

  if (!enabled || anchor == null || overlapsQuery.isLoading || overlap == null || overlap.partners.length === 0) {
    return null
  }

  const partnerCount = overlap.partners.length
  const label =
    partnerCount === 1
      ? 'Ещё у 1 в «Позже»'
      : `Ещё у ${partnerCount} в «Позже»`

  const handleAction = () => {
    if (onWatchTogether != null) {
      onWatchTogether()
      return
    }
    if (inViewerWatchlist === false) {
      void navigate(buildWatchlistNewHref(overlap))
      return
    }
    if (pendingPartners.length === 0) {
      return
    }
    setActionError(null)
    setConfirm({ item: overlap, partners: pendingPartners })
  }

  const showCreateCta = inViewerWatchlist === false
  const showInviteCta = inViewerWatchlist !== false && pendingPartners.length > 0
  const showAlreadyInvited = inViewerWatchlist !== false && pendingPartners.length === 0

  return (
    <>
      <div className="rounded-xl border border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_22%,var(--tgui--divider_color))] bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_8%,var(--tgui--secondary_bg_color))] p-3">
        <div className="flex items-start gap-2.5">
          <div className="flex -space-x-2 pt-0.5">
            {overlap.partners.slice(0, 4).map((partner) => (
              <Avatar
                key={partner.user_id}
                src={partner.avatar_url ?? undefined}
                acronym={partnerInitials(partner)}
                size={28}
              />
            ))}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-(--tgui--text_color)">{label}</p>
            <p className="mt-0.5 line-clamp-2 text-xs text-(--tgui--hint_color)">
              {overlap.partners.map((p) => partnerDisplayName(p)).join(', ')}
            </p>
          </div>
        </div>
        {actionError != null ? (
          <p className="mt-2 text-xs text-(--tgui--destructive_text_color)">{actionError}</p>
        ) : null}
        {showCreateCta ? (
          <Button size="s" stretched className="mt-3!" onClick={handleAction}>
            Смотрим вместе
          </Button>
        ) : null}
        {showInviteCta ? (
          <Button size="s" stretched className="mt-3!" onClick={handleAction} disabled={inviteMutation.isPending}>
            {inviteMutation.isPending ? 'Отправляем…' : 'Пригласить смотреть вместе'}
          </Button>
        ) : null}
        {showAlreadyInvited ? (
          <p className="mt-3 text-xs text-(--tgui--hint_color)">Друзья уже приглашены в этот просмотр</p>
        ) : null}
      </div>

      {confirm != null ? (
        <WatchTogetherConfirmSheet
          open
          mode="invite"
          title={confirm.item.title}
          posterUrl={confirm.item.poster_url}
          partners={confirm.partners}
          busy={inviteMutation.isPending}
          onClose={() => {
            if (!inviteMutation.isPending) {
              setConfirm(null)
            }
          }}
          onConfirm={() => {
            inviteMutation.mutate(confirm)
          }}
        />
      ) : null}
    </>
  )
}
