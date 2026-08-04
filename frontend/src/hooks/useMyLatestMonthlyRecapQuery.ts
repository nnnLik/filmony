import { useQuery } from '@tanstack/react-query'

import { getMyLatestMonthlyRecap } from '../api/profileApi'
import type { MonthlyRecap } from '../api/profileTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { myLatestMonthlyRecapQueryKey } from '../lib/profileQueryKeys'

export type UseMyLatestMonthlyRecapQueryOptions = {
  enabled?: boolean
}

export function useMyLatestMonthlyRecapQuery(options?: UseMyLatestMonthlyRecapQueryOptions) {
  const auth = useAuthStatus()
  const enabled = (options?.enabled ?? true) && auth.kind === 'ready'

  return useQuery<MonthlyRecap, Error>({
    queryKey: myLatestMonthlyRecapQueryKey(),
    queryFn: getMyLatestMonthlyRecap,
    enabled,
    staleTime: 10 * 60_000,
    gcTime: 30 * 60_000,
  })
}
