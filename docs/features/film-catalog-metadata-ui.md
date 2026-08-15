# Film catalog metadata UI

Compact presentation of Kinopoisk/TMDB passport data on film detail pages and movie cards.

## Components

| Piece | Role |
|-------|------|
| `FilmCatalogMetadata` | Orchestrator; `variant: 'compact' \| 'full'` |
| `FilmPassportInline` | Duration, age limit, colored KP/IMDb, trailer chip |
| `CollapsibleFilmMetaSection` | Expand/collapse for providers and similar titles (full pages) |

Display helpers live in `frontend/src/lib/filmCatalogMetadataDisplay.ts`.

## Pages

- **`FilmDetailPage`** — `variant="full"`: slogan, passport line, collapsible providers/similar, synopsis clamp.
- **`MovieCardDetailPage`** — `variant="compact"`: passport line + trailer; similar scroll hidden; fetches film passport via `getFilmById`.

## Trailer

- When `trailer_youtube_url` exists: labeled chip with ▶ opens YouTube.
- When missing: muted «Трейлер пока недоступен» chip (not clickable).

## Similar titles

API returns `tmdb_recommendations: FilmRecommendationItem[]` with `in_catalog`, optional `film_id`.

- In catalog → `/films/{film_id}` (solid pill).
- Not in catalog → `/search` with `state.cardsQuery` (dashed pill).

Resolver: `backend/src/services/films/resolve_tmdb_recommendations.py` (match by `tmdb_id`, then title).

## Verification

```bash
cd frontend && npm run lint && npm run build
cd frontend && npm run test -- --run src/lib/__tests__/filmCatalogMetadataDisplay.test.ts
make backend-test-one target=src/tests/unit/services/films/test_resolve_tmdb_recommendations.py
```
