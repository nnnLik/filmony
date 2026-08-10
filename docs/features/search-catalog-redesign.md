# Search catalog redesign

Redesigns the **Поиск** tab: default **Карточки** segment shows a paginated community film catalog (no query required); **Люди** segment keeps people suggestions and user search. Cards mode no longer mixes films, catalog topics, and users in one stream.

## Summary

| Before | After |
|--------|-------|
| Empty default until user types | **Карточки** opens with community film browse |
| Mixed cards + topics + people | **Карточки \| Люди** via `SegmentedControl` |
| No sort/period for films | **Популярные** / **Высший средний**; **За всё время** / **За месяц** |
| Film list via mixed `/api/search` | Dedicated `GET /api/catalog/films` with optional `q` filter |

## Backend

### `GET /api/catalog/films`

Authenticated browse endpoint for community-rated **films only** (no games).

| Param | Values | Default | Notes |
|-------|--------|---------|-------|
| `sort` | `popularity` \| `avg_rating` | `popularity` | popularity = `ratings_count` DESC; avg_rating = `community_avg_rating` DESC |
| `period` | `all_time` \| `month` | `all_time` | month = cards with `created_at` in last 30 days |
| `q` | string, optional | — | min 2 chars; title ILIKE filter; sort+period preserved |
| `cursor` | string, optional | — | opaque cursor pagination |
| `limit` | int | 20 | max 50 |

**Response:** `{ items: CatalogFilmItem[], next_cursor: string | null }`

**Item fields:** `film_id`, `title`, `year`, `poster_url`, `genres`, `community_avg_rating`, `ratings_count`, `my_card_id`

**Aggregation rules:**

- Source: rated `UserCard` rows (`is_planned == false`, `rating >= 1`) linked to `Film`.
- `period=all_time`: all matching cards.
- `period=month`: only cards with `UserCard.created_at >= now() - 30d`.
- `sort=popularity`: order by `ratings_count` DESC, then `film_id`.
- `sort=avg_rating`: order by `community_avg_rating` DESC; films with **fewer than 3** ratings excluded.

**Service:** `ListCatalogFilmsService` in `backend/src/services/catalog/list_catalog_films.py`

## Frontend

### Search page (`SearchPage.tsx`)

**Segments:** `Карточки` (default) | `Люди` — `SegmentedControl`; URL `?tab=people` selects Люди.

**Cards mode:**

- Period: `За всё время` (default) | `За месяц`
- Sort: `Популярные` (default) | `Высший средний`
- Search input placeholder: «Название фильма…» — `q` ≥ 2 chars filters server-side
- Infinite list via `useCursorInfiniteList` + `CatalogFilmsSection` (poster, title, year, ratings)
- Does **not** call mixed `/api/search` for the film list

**People mode:**

- `UserSuggestionChipsStrip` when query empty
- User search when `q` ≥ 2 via existing `/api/search` users API

### API client

- `listCatalogFilms()` in `frontend/src/api/catalogApi.ts`
- Types: `CatalogFilmsSort`, `CatalogFilmsPeriod`, `CatalogFilmItem`, `CatalogFilmsPage`

## Key files

- `backend/src/services/catalog/list_catalog_films.py`
- `backend/src/api/catalog/routes.py`
- `backend/src/api/catalog/schemas.py`
- `backend/src/tests/integration/api/test_catalog_films_list.py`
- `frontend/src/api/catalogApi.ts`
- `frontend/src/pages/SearchPage.tsx`
- `frontend/src/components/catalog/CatalogFilmsSection.tsx`

## Verification

```bash
make backend-test-one target=src/tests/integration/api/test_catalog_films_list.py
cd frontend && npm run lint && npm run build
```

Integration tests cover popularity sort, avg_rating min_ratings=3, month period (`created_at` window), `q` title filter, validation errors, and cursor pagination.

## Known limitations

- Global aggregation may be slow at scale without materialized counters.
- Month period uses `UserCard.created_at`, not a dedicated rated-at timestamp.
- `avg_rating` sort excludes films with &lt; 3 community ratings.
