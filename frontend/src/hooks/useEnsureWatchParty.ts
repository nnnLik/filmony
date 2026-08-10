import { useEffect, useState, type Dispatch, type SetStateAction } from 'react'
import { useNavigate } from 'react-router'

import {
  createWatchParty,
  getWatchParty,
  joinWatchParty,
  resolveWatchPartyBySlug,
} from '../api/watchPartyApi'
import { ApiError } from '../api/client'
import type { ActivePartyConflictDetail, WatchPartySnapshot } from '../api/watchPartyTypes'

function isActivePartyConflict(detail: unknown): detail is ActivePartyConflictDetail {
  return (
    typeof detail === 'object'
    && detail !== null
    && Reflect.get(detail, 'code') === 'already_in_active_party'
    && typeof Reflect.get(detail, 'invite_slug') === 'string'
  )
}

export type UseEnsureWatchPartyResult = {
  snapshot: WatchPartySnapshot | null
  setSnapshot: Dispatch<SetStateAction<WatchPartySnapshot | null>>
  loading: boolean
  error: string | null
}

export function useEnsureWatchParty(
  filmId: number,
  partySlug: string | null,
  enabled: boolean,
): UseEnsureWatchPartyResult {
  const navigate = useNavigate()
  const [snapshot, setSnapshot] = useState<WatchPartySnapshot | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!enabled || !Number.isFinite(filmId) || filmId < 1) {
      return undefined
    }

    let cancelled = false

    const ensureParty = async () => {
      setLoading(true)
      setError(null)
      try {
        let partyId: string
        let slug = partySlug?.trim() ?? ''

        if (slug !== '') {
          const resolved = await resolveWatchPartyBySlug(slug)
          partyId = resolved.party_id
        } else {
          try {
            const created = await createWatchParty(filmId)
            partyId = created.id
            slug = created.invite_slug
            void navigate(`/films/${filmId}/watch?party=${encodeURIComponent(slug)}`, { replace: true })
          } catch (createError) {
            if (
              createError instanceof ApiError
              && createError.status === 409
              && isActivePartyConflict(createError.detail)
            ) {
              slug = createError.detail.invite_slug
              void navigate(`/films/${filmId}/watch?party=${encodeURIComponent(slug)}`, { replace: true })
              const resolved = await resolveWatchPartyBySlug(slug)
              partyId = resolved.party_id
            } else {
              throw createError
            }
          }
        }

        let snap: WatchPartySnapshot
        try {
          snap = await getWatchParty(partyId)
        } catch (getError) {
          if (getError instanceof ApiError && getError.status === 403) {
            try {
              await joinWatchParty(partyId)
            } catch (joinError) {
              if (
                joinError instanceof ApiError
                && joinError.status === 409
                && isActivePartyConflict(joinError.detail)
              ) {
                const conflictSlug = joinError.detail.invite_slug
                void navigate(`/films/${filmId}/watch?party=${encodeURIComponent(conflictSlug)}`, {
                  replace: true,
                })
                return
              }
              throw joinError
            }
            snap = await getWatchParty(partyId)
          } else {
            throw getError
          }
        }

        if (!cancelled) {
          setSnapshot(snap)
        }
      } catch {
        if (!cancelled) {
          setError('Не удалось подключиться к просмотру')
          setSnapshot(null)
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void ensureParty()

    return () => {
      cancelled = true
    }
  }, [enabled, filmId, navigate, partySlug])

  return { snapshot, setSnapshot, loading, error }
}
