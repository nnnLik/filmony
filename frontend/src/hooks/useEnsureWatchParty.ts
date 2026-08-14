import { useEffect, useState, type Dispatch, type SetStateAction } from 'react'
import { useNavigate, type NavigateFunction } from 'react-router'

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

async function resolvePartyIdBySlug(slug: string): Promise<string> {
  const resolved = await resolveWatchPartyBySlug(slug)
  return resolved.party_id
}

async function resolvePartyIdBySlugOrNull(slug: string): Promise<string | null> {
  try {
    return await resolvePartyIdBySlug(slug)
  } catch (resolveError) {
    if (resolveError instanceof ApiError && resolveError.status === 404) {
      return null
    }
    throw resolveError
  }
}

async function createWatchPartyWithConflictHandling(
  filmId: number,
  navigate: NavigateFunction,
  allowConflictRetry: boolean,
): Promise<{ partyId: string; slug: string }> {
  try {
    const created = await createWatchParty(filmId)
    const newSlug = created.invite_slug
    void navigate(`/films/${filmId}/watch?party=${encodeURIComponent(newSlug)}`, { replace: true })
    return { partyId: created.id, slug: newSlug }
  } catch (createError) {
    if (
      createError instanceof ApiError
      && createError.status === 409
      && isActivePartyConflict(createError.detail)
    ) {
      const conflictSlug = createError.detail.invite_slug
      void navigate(`/films/${filmId}/watch?party=${encodeURIComponent(conflictSlug)}`, { replace: true })
      const conflictPartyId = await resolvePartyIdBySlugOrNull(conflictSlug)
      if (conflictPartyId !== null) {
        return { partyId: conflictPartyId, slug: conflictSlug }
      }
      if (allowConflictRetry) {
        return createWatchPartyWithConflictHandling(filmId, navigate, false)
      }
      throw createError
    }
    throw createError
  }
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
      queueMicrotask(() => {
        setLoading(false)
        setError(null)
        setSnapshot(null)
      })
      return undefined
    }

    let cancelled = false

    const ensureParty = async () => {
      setLoading(true)
      setError(null)
      try {
        let partyId: string
        const slug = partySlug?.trim() ?? ''

        if (slug !== '') {
          try {
            partyId = await resolvePartyIdBySlug(slug)
          } catch (resolveError) {
            if (resolveError instanceof ApiError && resolveError.status === 404) {
              const created = await createWatchPartyWithConflictHandling(filmId, navigate, true)
              partyId = created.partyId
            } else {
              throw resolveError
            }
          }
        } else {
          const created = await createWatchPartyWithConflictHandling(filmId, navigate, true)
          partyId = created.partyId
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
