import type { CardCompany, CardMoodAfter, CardMoodBefore } from './profileTypes'

export type TasteQuizCanPlayReason =
  | 'owner_insufficient_cards'
  | 'not_following'
  | 'active_session_exists'
  | null

export type TasteQuizCanPlayResponse = {
  can_play: boolean
  reason: TasteQuizCanPlayReason
  owner_rated_count: number
  requires_follow: boolean
  guesser_follows_owner: boolean
  active_session_id: string | null
  gate_min_rated_cards: number
}

export type TasteQuizSessionStatus = 'active' | 'completed' | 'abandoned'

export type TasteQuizVerdictKey = 'exact' | 'close' | 'miss'

export type TasteQuizSessionCard = {
  session_card_id: string
  card_id: number
  order_index: number
  title: string
  poster_url: string | null
  company: CardCompany
  mood_before: CardMoodBefore
  owner_rating: number | null
  mood_after: CardMoodAfter | null
  watch_note: string | null
  guess_rating: number | null
  round_points: number | null
  verdict_key: TasteQuizVerdictKey | null
  answered_at: string | null
}

export type TasteQuizSession = {
  id: string
  guesser_user_id: string
  owner_user_id: string
  status: TasteQuizSessionStatus
  card_count: number
  current_index: number
  round_points: number
  cards: TasteQuizSessionCard[]
  created_at: string
  completed_at: string | null
}

export type TasteQuizPairProgress = {
  points_sum: number
  attempts: number
  accuracy_pct: number
}

export type TasteQuizSubmitAnswerResponse = {
  card: TasteQuizSessionCard
  session: TasteQuizSession
  pair_progress: TasteQuizPairProgress
  session_completed: boolean
}

export type TasteQuizKnowledgeDirection = 'to_them' | 'to_me'

export type TasteQuizKnowledgeItem = {
  user_id: string
  profile_slug: string
  display_name: string | null
  avatar_url: string | null
  points_sum: number
  attempts: number
  accuracy_pct: number
}

export type TasteQuizKnowledgeListResponse = {
  items: TasteQuizKnowledgeItem[]
  next_cursor: string | null
}

export type TasteQuizKnowledgeBatchItem = {
  attempts: number
  accuracy_pct: number
  points_sum: number
}

export type TasteQuizKnowledgeBatchResponse = {
  items: Record<string, TasteQuizKnowledgeBatchItem>
}

export type TasteQuizCreateInviteResponse = {
  invite_token: string
  share_url: string | null
  telegram_share_text: string
}

export type TasteQuizInviteOwnerSnippet = {
  user_id: string
  profile_slug: string
  display_name: string | null
  avatar_url: string | null
}

export type TasteQuizResolveInviteResponse = {
  owner: TasteQuizInviteOwnerSnippet
  invite_token: string
  share_url: string | null
  can_play: boolean
  reason: TasteQuizCanPlayReason
  owner_rated_count: number
  gate_min_rated_cards: number
  expired: boolean
}
