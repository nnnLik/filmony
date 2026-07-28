import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getUserSubscriptions } from '../api/profileApi'
import { useAuthStatus } from '../auth/useAuthStatus'
import { MentionProfileLookupProvider } from '../context/MentionProfileLookupProvider'
import { authorLikeToMentionRow } from '../lib/mentionProfileLookupUtils'
import { subscriptionToMentionRow } from '../lib/subscriptionToMentionRow'
import { readMyProfileBundleCache } from '../lib/myProfileBundleCache'
import { scheduleIdleWork } from '../lib/scheduleIdleWork'

/**
 * Регистрирует профили из «мои подписки» и кэша своего профиля, чтобы @упоминания
 * в ленте/черновиках могли показать username и вести на `/u/:id`.
 */
export function MentionProfileLookupBootstrap({ children }: { children: ReactNode }) {
  const auth = useAuthStatus()
  const myUserId = auth.kind === 'ready' ? (readMyProfileBundleCache()?.profile.id ?? null) : null
  const [deferReady, setDeferReady] = useState(false)

  useEffect(() => {
    scheduleIdleWork(() => {
      queueMicrotask(() => {
        setDeferReady(true)
      })
    })
  }, [])

  const followingQuery = useQuery({
    queryKey: ['userSubscriptions', myUserId, 'following'],
    queryFn: () => getUserSubscriptions(myUserId as string, 'following'),
    enabled: myUserId != null && deferReady,
    staleTime: 60_000,
  })

  const value = useMemo(() => {
    const rows = []
    const bundle = readMyProfileBundleCache()
    if (bundle?.profile != null) {
      rows.push(authorLikeToMentionRow(bundle.profile))
    }
    for (const it of followingQuery.data?.items ?? []) {
      rows.push(subscriptionToMentionRow(it))
    }
    return rows
  }, [followingQuery.data])

  return <MentionProfileLookupProvider value={value}>{children}</MentionProfileLookupProvider>
}
