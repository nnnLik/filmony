export const ratingStreaksOfUsersQueryKey = (userIds: readonly string[]) =>
  ['streaks', 'batch', [...userIds].sort().join(',')] as const
