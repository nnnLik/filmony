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
  items: MovieCard[]
  next_cursor: string | null
}

export type CardCompany = 'alone' | 'partner' | 'friends' | 'family'
export type CardMoodBefore = 'relax' | 'laugh' | 'sad' | 'thrill'
export type CardMoodAfter = 'laughed' | 'cried' | 'enjoyed' | 'tense' | 'wasted_time'

export type MovieCard = {
  id: number
  film_id: number
  film_title: string
  film_year: number | null
  film_poster_url: string | null
  rating: number
  company: CardCompany
  mood_before: CardMoodBefore
  mood_after: CardMoodAfter
  custom_tags: string[]
}

export type Film = {
  id: number
  kinopoisk_id: number
  title: string
  year: number | null
  poster_url: string | null
}
