import { Button, IconButton } from '@telegram-apps/telegram-ui'
import { X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'

import { inviteWatchPartyMembers } from '../../api/watchPartyApi'
import { getMyProfile, getUserSubscriptions } from '../../api/profileApi'
import { ApiError, formatApiDetail } from '../../api/client'
import { MutualWatchFriendsMultiPicker } from '../watchlist/MutualWatchFriendsMultiPicker'
import { filterMutualSubscriptions } from '../../lib/mutualSubscriptionFilter'

export type WatchPartyInviteSheetProps = {
  open: boolean
  partyId: string
  onClose: () => void
}

export function WatchPartyInviteSheet({ open, partyId, onClose }: WatchPartyInviteSheetProps) {
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([])
  const [loadingFriends, setLoadingFriends] = useState(false)
  const [friends, setFriends] = useState<ReturnType<typeof filterMutualSubscriptions>>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) {
      return undefined
    }
    let alive = true
    queueMicrotask(() => {
      if (alive) {
        setLoadingFriends(true)
      }
    })
    void (async () => {
      try {
        const me = await getMyProfile()
        const subs = await getUserSubscriptions(me.id, 'both')
        if (!alive) return
        setFriends(filterMutualSubscriptions(subs.items))
      } catch {
        if (!alive) return
        setFriends([])
      } finally {
        if (alive) setLoadingFriends(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [open])

  const memberIds = useMemo(() => new Set(selectedUserIds), [selectedUserIds])

  const toggleUser = (userId: string) => {
    setSelectedUserIds((prev) =>
      prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId],
    )
  }

  const submit = async () => {
    if (memberIds.size === 0) {
      return
    }
    setBusy(true)
    setError(null)
    try {
      await inviteWatchPartyMembers(partyId, [...memberIds])
      setSelectedUserIds([])
      onClose()
    } catch (e) {
      if (e instanceof ApiError) {
        setError(formatApiDetail(e.detail))
      } else {
        setError('Не удалось отправить приглашения')
      }
    } finally {
      setBusy(false)
    }
  }

  if (!open) {
    return null
  }

  return createPortal(
    <div className="filmony-theme fixed inset-0 z-50 flex flex-col justify-end text-(--tgui--text_color) pointer-events-auto">
      <button
        type="button"
        className="absolute inset-0 bg-[color-mix(in_srgb,var(--filmony-ink,#06090d)_72%,transparent)]"
        aria-label="Закрыть"
        onClick={onClose}
      />
      <div
        className="relative z-10 mx-auto flex max-h-[80dvh] w-full max-w-md flex-col rounded-t-[22px] border border-(--tgui--divider_color) bg-(--tgui--tertiary_bg_color) p-4 shadow-[0_-16px_48px_rgba(0,0,0,0.5)]"
        role="dialog"
        aria-modal="true"
      >
        <div className="mb-3 flex shrink-0 items-center justify-between gap-2">
          <h2 className="text-lg font-semibold">Пригласить друзей</h2>
          <IconButton mode="gray" size="s" onClick={onClose} aria-label="Закрыть" disabled={busy}>
            <X className="block size-5" />
          </IconButton>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto">
          <MutualWatchFriendsMultiPicker
            friends={friends}
            loading={loadingFriends}
            selectedUserIds={selectedUserIds}
            onToggle={toggleUser}
          />
        </div>
        {error != null ? <p className="mt-2 text-sm text-red-400">{error}</p> : null}
        <Button
          className="mt-3 shrink-0"
          stretched
          disabled={busy || selectedUserIds.length === 0}
          onClick={() => void submit()}
        >
          {busy ? 'Отправляем…' : 'Пригласить'}
        </Button>
      </div>
    </div>,
    document.body,
  )
}
