export const STREAK_BATCH_MAX_USER_IDS = 100
export const STREAK_BATCH_MIN_CURRENT = 4

export type StreakBatchItem = {
  current: number
}

export type StreakBatchResponse = {
  items: Record<string, StreakBatchItem>
}

export type MyStreakResponse = {
  current: number
}
