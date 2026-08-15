import type { QueryClient } from '@tanstack/react-query'
import { profileQueryRootKey } from './profileQueryKeys'
import { clearActivityHeatmapSessionCaches } from './activityHeatmapCache'

export function invalidateProfileAggregates(queryClient: QueryClient): void {
  void queryClient.invalidateQueries({ queryKey: profileQueryRootKey })
  clearActivityHeatmapSessionCaches()
}
