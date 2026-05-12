/** Строка пикера «просмотренных» карточек для вставки в текст. Без зависимостей от `profileTypes` / `cardApi`. */

export type WatchedInlinePickerItem = {
  movie_card_id: number
  film_title: string
  film_year: number | null
}
