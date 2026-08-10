# Search Catalog Redesign — Implementation Plan

> **Status:** `completed`

## Locked product decisions

1. **Films only** — catalog browse excludes games and non-film catalog types.
2. **SegmentedControl «Карточки | Люди»** — default «Карточки»; Cards mode never mixes people or catalog topics.
3. **Two sorts in Cards mode:** «Популярные» (`ratings_count` DESC) and «Высший средний» (`community_avg_rating` DESC). No separate «Больше всего оценок» — same metric as Popular.
4. **Period filter:** «За всё время» (default) | «За месяц» (last 30 days of `UserCard.created_at`); applies to both count and avg.
5. **Single browse endpoint with `q` as filter** — empty `q` = browse; `q` ≥ 2 chars filters the same list server-side; Cards mode does not use mixed `/api/search` for the film list.

## Chosen search behavior

- One browse endpoint; `q` is a server-side filter on the current sort+period.
- Empty `q` → browse; non-empty (min 2 chars) → filtered same list.
- **Why:** one API contract, consistent pagination/sort/period, less UI mode switching, better perceived speed.
- Do not reintroduce mixed cards+topics+people in Cards mode.

## UX (RU labels)

**Segments:** `Карточки` | `Люди` (default Карточки)

**Cards mode controls:**

- Search input placeholder e.g. «Название фильма…»
- Period segmented/chips: `За всё время` (default) | `За месяц`
- Sort: `Популярные` (default) | `Высший средний`

**People mode:** keep chips + «человек» search via existing APIs; no film catalog.

## Backend

**Endpoint:** `GET /api/catalog/films` (new; fits `/api/catalog/*` and mirrors genre film list shape)

**Query params:**

| Param | Values | Default | Notes |
|-------|--------|---------|-------|
| `sort` | `popularity` \| `avg_rating` | `popularity` | popularity = `ratings_count` DESC; avg_rating = `community_avg_rating` DESC |
| `period` | `all_time` \| `month` | `all_time` | month = last 30 days of UserCard activity (`created_at` window) used for both count and avg |
| `q` | string optional | — | when present: min 2 chars; ILIKE/title filter on films; still apply sort+period |
| `cursor` | string optional | — | opaque, same style as genre films |
| `limit` | int | 20 | max 50 |

**Aggregation rules (reuse):**

- Source: `UserCard` with `is_planned == false`, `rating >= 1`, linked to Film (films only — exclude games/catalog game types).
- `period=all_time`: all matching cards.
- `period=month`: only cards with `created_at >= now() - 30d` (document this definition).
- `ratings_count` = **count of rated cards** matching filters — mirror `GetCatalogCommunityStatsService` semantics exactly (`func.count(UserCard.id)` with `_rated_card_filters()`).
- `community_avg_rating` = mean of those ratings (`func.avg(UserCard.rating)`, rounded to 1 decimal).

**Response:** `{ items: [...], next_cursor: string|null }`

Item fields aligned with `GenreFilmItemResponse`:

- `film_id`, `title`, `year`, `poster_url`, `genres`, `community_avg_rating`, `ratings_count`, `my_card_id` (optional but useful)

**Service:** new verb-named service e.g. `ListCatalogFilmsService` with `build`/`execute`; thin route; DAO for aggregation query; compose/reuse community-stats filters where practical.

**Tests:** unit for sort/period/q edge cases with mocked DAO if pure; integration for route happy path, validation (bad sort/period, q too short), pagination cursor, films-only.

**Keep:** `GET /api/search` for People mode (users) and any card-author search if still needed in People; Cards mode should NOT call mixed `/api/search` for the film list.

## Frontend

**Page structure (`SearchPage.tsx`):**

1. Page header title «Поиск»
2. SegmentedControl Карточки|Люди
3. If Карточки:
   - period control + sort control
   - search input
   - infinite/cursor list of film rows (poster, title, year, ratings_count, community_avg_rating) → navigate to existing film/community path
   - empty/loading/error via `TabEmptyState` / existing patterns
4. If Люди:
   - existing `UserSuggestionChipsStrip` when `q` empty
   - people results when `q` ≥ 2 via existing search users API

**API client:** new function in `catalogApi.ts` or `searchApi.ts` for `GET /api/catalog/films`

**State:** segment in local state or `?tab=cards|people` (prefer URL `?tab=` for shareability if `SubscriptionsPage` pattern exists — optional note)

## Implementation steps (ordered)

1. Backend: `ListCatalogFilmsService` + DAO query + route + response schemas + integration tests
2. Frontend: API client types
3. Frontend: SearchPage SegmentedControl + Cards browse UI (sort/period/q/pagination)
4. Frontend: People segment wire-up (extract current people UX)
5. Remove/stop using mixed three-section results in Cards mode
6. Lint/build frontend; backend tests in Docker
7. Docs + `result.md` + closeout (later)

## Open technical risks (max 3)

1. **Global aggregation + sort performance** without materialized counters — may need SQL indexes / limited window / later cache.
2. **`period=month` not in existing community-stats services** — new query path; define `created_at` vs `rated_at` (use `created_at`).
3. **`avg_rating` sort: low-count films can dominate** — recommend `min_ratings=3` for `avg_rating` sort only (v1 default to confirm at approval); `popularity` sort has no minimum.

## Approval gate

User must explicitly approve before any product code.

**Ask:** «Можно начинать реализацию? (да/нет)»
