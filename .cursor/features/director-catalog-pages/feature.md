# Director catalog pages

## Scope
- Show primary director on movie cards (detail, feed, film page) with unique color chip linking to director page.
- New `/directors/:kinopoiskId` page listing rated films in Filmony for that director (avg rating, genres).
- Film row links to existing `/films/:id` with all user ratings.

## Acceptance criteria
- `GET /api/directors/{kinopoisk_id}` and `/films` endpoints return summary + paginated rated films only.
- Card/feed/film API expose `film_primary_director_*` fields when enriched.
- DirectorChip navigates to director page; director page navigates to film page.
- pytest coverage for director routes; frontend lint/build pass.

## Out of scope
- Kinopoisk person API, multi-director, director index browse, RAWG items without director.
