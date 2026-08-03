export function myGamificationQueryKey(): readonly ['gamification', 'me'] {
  return ['gamification', 'me'] as const
}

export function userPassportQueryKey(userId: string): readonly ['gamification', 'passport', string] {
  return ['gamification', 'passport', userId] as const
}
