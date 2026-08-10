import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router'

import { createWatchParty } from '../api/watchPartyApi'
import { ApiError } from '../api/client'
import type { ActivePartyConflictDetail } from '../api/watchPartyTypes'
import { WatchPartyCreateSheet } from '../components/watchparty/WatchPartyCreateSheet'

function isActivePartyConflict(detail: unknown): detail is ActivePartyConflictDetail {
  return (
    typeof detail === 'object'
    && detail !== null
    && Reflect.get(detail, 'code') === 'already_in_active_party'
    && typeof Reflect.get(detail, 'invite_slug') === 'string'
  )
}

export function useWatchPartyCreateFlow(filmId: number, title: string, posterUrl: string | null) {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)

  const openSheet = useCallback(() => {
    setOpen(true)
  }, [])

  const closeSheet = useCallback(() => {
    if (!busy) {
      setOpen(false)
    }
  }, [busy])

  const confirmCreate = useCallback(async () => {
    if (!Number.isFinite(filmId) || filmId < 1) {
      return
    }
    setBusy(true)
    try {
      const created = await createWatchParty(filmId)
      setOpen(false)
      void navigate(`/watch-party/${created.invite_slug}`, { replace: false })
    } catch (error) {
      if (error instanceof ApiError && error.status === 409 && isActivePartyConflict(error.detail)) {
        setOpen(false)
        void navigate(`/watch-party/${error.detail.invite_slug}`, { replace: false })
        return
      }
    } finally {
      setBusy(false)
    }
  }, [filmId, navigate])

  const sheet = (
    <WatchPartyCreateSheet
      open={open}
      title={title}
      posterUrl={posterUrl}
      busy={busy}
      onClose={closeSheet}
      onConfirm={() => {
        void confirmCreate()
      }}
    />
  )

  return { openSheet, sheet }
}
