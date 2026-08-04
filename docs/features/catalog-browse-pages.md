# Catalog browse pages

Community discovery for directors and genres.

## API
- `GET /api/directors` — paginated director index
- `GET /api/genres` — genre index with `films_count`
- `GET /api/genres/{slug}`, `/{slug}/films`
- `GET /api/users/{id}/cards?genre=` — personal drill-down by genre slug
- Stats include `genre_distribution`

## UI
- `/directors`, `/genres`, `/genres/:slug`
- Profile stats genre donut → `?genre=`; director filter link → `/directors`
