export type WeeklyControversyItem = {
  anchor_film_id: number | null
  anchor_catalog_item_id: number | null
  title: string
  spread: number
  rater_count: number
  min_rating: number
  max_rating: number
}

export type WeeklyControversyResponse = {
  week_start: string
  controversy: WeeklyControversyItem | null
}
