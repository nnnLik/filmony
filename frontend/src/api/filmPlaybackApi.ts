import { apiJson } from './client'

export type FilmPlaybackResponse = {
  provider: string
  title: string
  iframe_url: string
  film_id: number
  kinopoisk_id: number
  expires_at: string
}

export async function getFilmPlayback(filmId: number): Promise<FilmPlaybackResponse> {
  return apiJson<FilmPlaybackResponse>(`/api/films/${filmId}/playback`)
}
