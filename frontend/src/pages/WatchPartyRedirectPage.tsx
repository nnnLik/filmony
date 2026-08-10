import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router'

import { getWatchParty, joinWatchParty, resolveWatchPartyBySlug } from '../api/watchPartyApi'
import { ApiError } from '../api/client'
import type { ActivePartyConflictDetail } from '../api/watchPartyTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { PageLoadingState } from '../components/ui/PageLoadingState'

function isActivePartyConflict(detail: unknown): detail is ActivePartyConflictDetail {
  return (
    typeof detail === 'object'
    && detail !== null
    && Reflect.get(detail, 'code') === 'already_in_active_party'
    && typeof Reflect.get(detail, 'invite_slug') === 'string'
  )
}

export function WatchPartyRedirectPage() {
  const auth = useAuthStatus()
  const navigate = useNavigate()
  const { inviteSlug } = useParams<{ inviteSlug: string }>()

  useEffect(() => {
    if (auth.kind === 'unauthenticated') {
      void navigate(`/login?returnTo=${encodeURIComponent(window.location.pathname)}`, { replace: true })
    }
  }, [auth.kind, navigate])

  useEffect(() => {
    if (auth.kind !== 'ready' || inviteSlug == null || inviteSlug.trim() === '') {
      return undefined
    }

    let cancelled = false

    const redirect = async () => {
      try {
        const resolved = await resolveWatchPartyBySlug(inviteSlug)
        let snap
        try {
          snap = await getWatchParty(resolved.party_id)
        } catch (error) {
          if (error instanceof ApiError && error.status === 403) {
            try {
              await joinWatchParty(resolved.party_id)
            } catch (joinError) {
              if (
                joinError instanceof ApiError
                && joinError.status === 409
                && isActivePartyConflict(joinError.detail)
              ) {
                void navigate(`/watch-party/${joinError.detail.invite_slug}`, { replace: true })
                return
              }
              throw joinError
            }
            snap = await getWatchParty(resolved.party_id)
          } else {
            throw error
          }
        }

        if (!cancelled) {
          void navigate(
            `/films/${snap.film_id}/watch?party=${encodeURIComponent(snap.invite_slug)}`,
            { replace: true },
          )
        }
      } catch {
        if (!cancelled) {
          void navigate('/search', { replace: true })
        }
      }
    }

    void redirect()

    return () => {
      cancelled = true
    }
  }, [auth.kind, inviteSlug, navigate])

  if (auth.kind === 'loading' || auth.kind === 'error') {
    return <PageLoadingState authPending className="min-h-dvh bg-black" />
  }

  return <PageLoadingState message="Открываем комнату…" className="min-h-dvh bg-black" />
}
