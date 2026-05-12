import { useQuery } from '@tanstack/react-query'
import { useMemo, type ReactNode } from 'react'

import { getUserSubscriptions } from '../api/profileApi'
import { useAuthStatus } from '../auth/useAuthStatus'
import { MentionProfileLookupProvider } from '../context/MentionProfileLookupProvider'
import { authorLikeToMentionRow } from '../lib/mentionProfileLookupUtils'
import { subscriptionToMentionRow } from '../lib/subscriptionToMentionRow'
import { readMyProfileBundleCache } from '../lib/myProfileBundleCache'

/**
 * Регистрирует профили из «мои подписки» и кэша своего профиля, чтобы @упоминания
 * в ленте/черновиках могли показать username и вести на `/u/:id`.
 */
export function MentionProfileLookupBootstrap({ children }: { children: ReactNode }) {
  const auth = useAuthStatus()
  const myUserId = auth.kind === 'ready' ? (readMyProfileBundleCache()?.profile.id ?? null) : null

  const followingQuery = useQuery({
    queryKey: ['userSubscriptions', myUserId, 'following'],
    queryFn: () => getUserSubscriptions(myUserId as string, 'following'),
    enabled: myUserId != null,
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
