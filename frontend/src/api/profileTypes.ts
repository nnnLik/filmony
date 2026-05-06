export type MyProfile = {
  id: string
  telegram_user_id: number
  username: string | null
  first_name: string | null
  last_name: string | null
  photo_url: string | null
  language_code: string | null
  profile_slug: string
  display_name: string | null
  bio: string | null
  cards_count: number
  friends_count: number
}

export type PublicProfile = {
  id: string
  profile_slug: string
  username: string | null
  first_name: string | null
  last_name: string | null
  photo_url: string | null
  display_name: string | null
  bio: string | null
  cards_count: number
  friends_count: number
}

export type MovieCardPage = {
  items: unknown[]
  next_cursor: string | null
}
