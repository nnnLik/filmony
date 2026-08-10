import { useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'

import { batchWatchingNow } from '../api/watchPartyWatchingApi'
import {
  WATCHING_NOW_BATCH_MAX_USER_IDS,
  type WatchingNowBatchItem,
  type WatchingNowBatchResponse,
} from '../api/watchPartyTypes'
import { useAuthStatus } from '../auth/useAuthStatus'

export type UseWatchingNowOfUsersOptions = {
  enabled?: boolean
  staleTime?: number
  gcTime?: number
  refetchInterval?: number | false
}

function normalizeUserIds(userIds: readonly string[]): string[] {
  const unique = [...new Set(userIds.filter((id) => id.trim() !== ''))]
  return unique.slice(0, WATCHING_NOW_BATCH_MAX_USER_IDS).sort()
}

export function watchingNowOfUsersQueryKey(userIds: readonly string[]) {
  return ['watching-now-batch', normalizeUserIds(userIds)] as const
}

export function useWatchingNowOfUsers(
  userIds: readonly string[],
  options?: UseWatchingNowOfUsersOptions,
) {
  const auth = useAuthStatus()
  const sortedIds = useMemo(() => normalizeUserIds(userIds), [userIds])

  const enabled = (options?.enabled ?? true) && auth.kind === 'ready' && sortedIds.length > 0

  const query = useQuery<WatchingNowBatchResponse, Error>({
    queryKey: watchingNowOfUsersQueryKey(sortedIds),
    queryFn: () => batchWatchingNow(sortedIds),
    enabled,
    ...(options?.staleTime != null ? { staleTime: options.staleTime } : {}),
    ...(options?.gcTime != null ? { gcTime: options.gcTime } : {}),
    ...(options?.refetchInterval != null ? { refetchInterval: options.refetchInterval } : {}),
  })

  const watchingByUserId: Record<string, WatchingNowBatchItem> = query.data?.items ?? {}

  return {
    ...query,
    watchingByUserId,
  }
}
