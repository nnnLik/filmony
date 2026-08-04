export type ShelfPhysicsMode = 'neutral' | 'slump' | 'glow'

export type ShelfPhysics = {
  mode: ShelfPhysicsMode
  streak_length: number
}

export type PassportStamp = {
  stamp_id: string
  title?: string | null
  description?: string | null
  unlocked: boolean
  unlocked_at?: string | null
  unlock_card_id?: number | null
  unlock_film_title?: string | null
  /** Primary poster field from API. */
  unlock_film_poster_url?: string | null
  /** Legacy alias kept for backward compatibility. */
  unlock_poster_url?: string | null
  progress_current?: number | null
  progress_target?: number | null
}

export type PassportSummary = {
  stamps: PassportStamp[]
  unlocked_count: number
}

export type MarathonKind = 'director' | 'franchise'

export type MarathonAchievement = {
  kind: MarathonKind
  key: string
  label: string
  count: number
  unlocked_at: string
  sample_poster_urls: string[]
}

export type GamificationResponse = {
  passport: PassportSummary
  marathons: MarathonAchievement[]
  shelf_physics: ShelfPhysics
}

export type PublicPassportResponse = {
  stamps: PassportStamp[]
  unlocked_count: number
}
