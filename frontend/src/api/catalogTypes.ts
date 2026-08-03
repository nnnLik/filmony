import type { FilmCommunityAuthor, FilmCommunityCardItem } from './profileTypes'

export type CatalogDetailKind = 'film' | 'game'

export type CatalogItemDetail = {
  catalog_item_id: number
  provider: string
  external_id: string
  kind: CatalogDetailKind
  title: string
  year: number | null
  poster_url: string | null
  short_description: string | null
  description: string | null
  film_id: number | null
  game_id: number | null
  genres: string[]
  my_card_id: number | null
}

export type CommunityCardItem = FilmCommunityCardItem
export type CommunityAuthor = FilmCommunityAuthor

export type CatalogCommunityCardsPage = {
  items: CommunityCardItem[]
  next_cursor: string | null
}
