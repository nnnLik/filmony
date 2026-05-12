import type { ReferencedInlineMovieCardSnippet } from '../api/profileTypes'

export type InlineMovieCardRefMeta = {
  film_title: string
  film_year: number | null
}

export function inlineMovieCardRefMapFromSnippets(
  snippets: ReferencedInlineMovieCardSnippet[] | null | undefined,
): ReadonlyMap<number, InlineMovieCardRefMeta> | undefined {
  if (snippets == null || snippets.length === 0) {
    return undefined
  }
  return new Map(
    snippets.map((s) => [
      s.movie_card_id,
      { film_title: s.film_title, film_year: s.film_year },
    ]),
  )
}
