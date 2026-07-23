export const tasteQuizCanPlayQueryKey = (ownerId: string, inviteToken?: string | null) =>
  ['tasteQuiz', 'canPlay', ownerId, inviteToken ?? ''] as const

export const tasteQuizSessionQueryKey = (sessionId: string) =>
  ['tasteQuiz', 'session', sessionId] as const

export const tasteQuizKnowledgeListQueryKey = (direction: string, cursor?: string | null) =>
  ['tasteQuiz', 'knowledge', direction, cursor ?? ''] as const

export const tasteQuizKnowledgeBatchQueryKey = (ownerId: string, guesserUserIds: readonly string[]) =>
  ['tasteQuiz', 'knowledgeBatch', ownerId, [...guesserUserIds].sort().join(',')] as const

export const tasteQuizResolveInviteQueryKey = (token: string) =>
  ['tasteQuiz', 'invite', token] as const
