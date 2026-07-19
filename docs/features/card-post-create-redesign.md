# Card / Post Create Redesign

## Summary

Redesigned how users create content from the feed: one **«Создать»** entry point opens an action sheet with three choices — **Карточка**, **Пост**, **Позже**. The four-step rated-card wizard is replaced by a smart search screen and a single scroll form. Watchlist («Позже») moved to a dedicated `/watchlist/new` route. Catalog providers (Kinopoisk, RAWG) are **Sources** that return unified **Candidates**, not card types.

**Spec:** `docs/superpowers/specs/2026-07-19-card-post-create-redesign-design.md`

## UX decisions

| Area | Before | After |
|------|--------|-------|
| Feed entry | Two icons (+ → `/cards/new`, pen → compose) | One **«Создать»** → bottom sheet |
| Sheet items | Card + post only | **Карточка \| Пост \| Позже** with subtitles |
| Card first screen | Provider/type picker + 4-step wizard | **Smart field** «Название или ссылка» |
| Catalog search | Per-provider queries | **Mixed candidates** (`GET /api/catalog/candidates`) |
| Film vs game conflict | Server auto-pick | **User picks row**; `kind_hint` only for UI grouping |
| After pick | Multi-step wizard | **One scroll form** (rating, shelf, moods, tags, note) |
| Watchlist | Branch inside rated wizard | **Separate short form** at `/watchlist/new` |
| Cover | URL hunt / limited upload | **Always preview + three equal actions:** Загрузить / Ссылка / Буфер |
| Post compose | Separate pen icon | Same `FeedComposeSheet`; clearer entry via sheet |

## Flows

### Feed → action sheet

1. Tap **«Создать»** in feed header.
2. Choose:
   - **Карточка** → `/cards/new` (new UX)
   - **Пост** → opens `FeedComposeSheet`
   - **Позже** → `/watchlist/new`

Two taps from feed to the card smart field.

### Rated card (`/cards/new`)

**Screen A — search / pick**

- Single field: «Название или ссылка».
- Text query → debounced `GET /api/catalog/candidates?q=…`.
- URL detected → `POST /api/catalog/resolve-by-url` (Kinopoisk in v1).
- Mixed candidate list with kind icon, subtitle, thumbnail.
- **«Создать вручную»** always available → manual binding.

**Screen B — scroll form**

- Read-only topic chip with «Изменить» back to Screen A.
- Cover block (preview + upload / link / buffer).
- Rating, shelf, company, moods, tags, note.
- Submit → existing `POST /api/cards`.
- Success → `/cards/:id`; share/audio remain secondary after create.
- Duplicate card warning unchanged (409 → link to existing card).

### Watchlist (`/watchlist/new`)

- Entry only from action sheet (not from rated form).
- Same smart field + pick/manual as card entry.
- Compact fields: company, watch-with friends, note — no rating/mood/tags.
- Submit → existing watchlist create + feed post side-effect.

### Post

- `FeedComposeSheet` unchanged; placeholder clarified to «Мысль, ссылка, упоминание…».
- Image upload via existing feed post upload endpoint.

## API

### New endpoints

#### `GET /api/catalog/candidates`

Mixed search across Kinopoisk and RAWG Sources.

**Query:** `q` (required), `limit` (default 15), `page` (default 1).

**Response:**

```json
{
  "items": [{ "candidate_id", "provider", "external_id", "kind", "title", "subtitle", "cover_url", "catalog_item_id", "source", "degraded?" }],
  "has_more": false,
  "meta": { "degraded_sources": ["rawg"] }
}
```

- Local hits first, then remote.
- Partial results when one Source fails (`meta.degraded_sources`).
- Same title film + game are **not** deduplicated.

#### `POST /api/catalog/resolve-by-url`

**Body:** `{ "url": "https://..." }`

- Kinopoisk hosts only in v1; other hosts → 422.
- Success → candidate prefill + optional `film` embed.
- Fail → 404/422; client offers manual path.

#### `POST /api/cards/covers/upload`

**Request:** `multipart/form-data`, field `file`.

**Response:** `{ "url": "/api/cards/media/…" }`

Same size/MIME limits as feed post image upload.

### Unchanged write contracts

- `POST /api/cards` — rated card create (fills `catalog_item_id`, `provider`, `display_*` from binding).
- `POST /api/me/watchlist` / `POST /api/watchlist` — watchlist entry.
- `POST /api/feed-posts` — feed post compose.

## Backend services

| Service | Role |
|---------|------|
| `SearchCatalogCandidatesService` | Parallel Source search, merge, sort, degraded meta |
| `ResolveCatalogByUrlService` | URL → Source delegation (Kinopoisk) |
| `UploadUserCardCoverService` | Card cover upload (shared pattern with feed image upload) |
| `CatalogCandidateDTO` | Unified candidate shape for API |

## Frontend components

| Path | Purpose |
|------|---------|
| `CreateActionSheet` | Feed bottom sheet: card / post / watchlist |
| `CreateCardPage` | Screen A (smart field) + Screen B (scroll form) |
| `CreateWatchlistPage` | Dedicated watchlist create |
| `CatalogCandidatesList` | Mixed candidate picker |
| `RatedCardScrollForm` | Single-page rated card form |
| `WatchlistForm` | Compact watchlist form |
| `CardCoverBlock` | Preview + upload / link / buffer |
| `useCatalogCandidates` | Debounced candidates query hook |
| `useResolveCatalogUrl` | URL resolve hook |
| `createCardBinding` / `watchlistBinding` | Client-side form binding from candidate/manual |

## Deep links & migration

| Entry | Behavior |
|-------|----------|
| `/cards/new` | New UX (no legacy wizard) |
| `/watchlist/new` | New watchlist form |
| `FilmDetailPage` «Позже» | Navigates to `/watchlist/new` with prefill params |
| Profile FAB | Unchanged (out of scope) |

## Error handling

| Situation | UX |
|-----------|-----|
| One Source timeout | Partial list + degraded hint |
| Both Sources fail | Empty list + «Создать вручную» |
| Resolve URL fail | Toast + manual CTA |
| Duplicate card | Existing warning + link |
| Upload fail | Inline error under preview |

## Tests

- `backend/src/tests/api/test_catalog_routes.py` — candidates, resolve-by-url, degraded sources
- `backend/src/tests/api/test_cards_routes.py` — cover upload auth/success/MIME
- `backend/src/tests/services/catalog/test_search_catalog_candidates_service.py` — service unit tests
