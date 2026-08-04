import { useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'

import { getMyProfile } from '../api/profileApi'
import type { MyProfile } from '../api/profileTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { readMyProfileBundleCache } from '../lib/myProfileBundleCache'
import { myProfileQueryKey } from '../lib/profileQueryKeys'

export type UseMyProfileQueryOptions = {
  enabled?: boolean
}

export function useMyProfileQuery(options?: UseMyProfileQueryOptions) {
  const auth = useAuthStatus()
  const enabled = (options?.enabled ?? true) && auth.kind === 'ready'
  const initialBundle = useMemo(() => readMyProfileBundleCache(), [])

  return useQuery<MyProfile, Error>({
    queryKey: myProfileQueryKey(),
    queryFn: getMyProfile,
    enabled,
    staleTime: 2 * 60_000,
    gcTime: 30 * 60_000,
    initialData: initialBundle?.profile,
    initialDataUpdatedAt: initialBundle?.storedAt,
  })
}
