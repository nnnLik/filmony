# YouTube card source

## Summary

YouTube is a **Source** for the card create flow (v1): paste a `youtube.com` / `youtu.be` link in the smart field on `/cards/new` or `/watchlist/new` → `POST /api/catalog/resolve-by-url` → prefill title/thumbnail/description → create an **abstract** `UserCard` with `provider=youtube`, `kind=video`, no `catalog_item`.

Metadata comes from **YouTube public oEmbed** (no YouTube Data API / API key). Cards persist as abstract subjects keyed by `(user_id, provider=youtube, external_id=<videoId>)`.

**Spec baseline:** `docs/superpowers/specs/2026-07-19-card-post-create-redesign-design.md` § Future: YouTube  
**Parent UX:** [`card-post-create-redesign.md`](./card-post-create-redesign.md)

## Scope (v1)

**In scope:**

- URL resolve only for YouTube hosts: `youtube.com`, `www.youtube.com`, `m.youtube.com`, `youtu.be`
- Supported path shapes: `/watch?v=`, `/shorts/`, `/embed/`, `youtu.be/<id>`
- oEmbed metadata: title, thumbnail, author name (mapped to card summary)
- Abstract card: `provider=youtube`, `external_id`, `display_*`, `source_url`, `catalog_item_id=null`, `film_id=null`
- Extend resolve response with `kind: 'video'` alongside Kinopoisk `kind: 'film'`
- Duplicate warning by `(user_id, provider=youtube, external_id)` — partial unique index + 409 on create
- Frontend bindings, labels («YouTube», «видео»), smart-field copy on card and watchlist create pages

**Non-goals (v1):**

- YouTube text search in `GET /api/catalog/candidates`
- YouTube Data API v3 / quota management
- `catalog_item` row for videos
- Feed card visual redesign for video cards
- Playlist / channel import

## Backend architecture

```
URL paste → ResolveCatalogByUrlService (host routing)
              ├─ kinopoisk.ru → existing catalog/film resolve
              └─ YouTube host → ResolveYoutubeVideoByUrlService
                                    ├─ parse_video_id (youtube_url.py)
                                    └─ YoutubeOembedClient.fetch (oEmbed)
```

### URL parsing

`backend/src/providers/youtube/youtube_url.py`

- `is_youtube_host(url)` — host detection
- `parse_video_id(url)` — 11-char video id from watch, youtu.be, shorts, embed paths
- `canonical_youtube_url(video_id)` — `https://www.youtube.com/watch?v=<id>`

### oEmbed client

`backend/src/providers/youtube/youtube_oembed_client.py`

- `GET https://www.youtube.com/oembed?url=<canonical>&format=json`
- 404 → `VideoNotFoundError`; transport/parse failures → `UpstreamError`

### Resolve service

`backend/src/services/catalog/resolve_youtube_video_by_url_service.py`

- `ResolveYoutubeVideoByUrlService.build().execute(url=…)` → `YoutubeVideoDTO`
- Errors: `UnsupportedUrlError`, `VideoNotFoundError`, `UpstreamError`

### Host routing

`backend/src/services/catalog/resolve_catalog_by_url_service.py` delegates YouTube hosts to the YouTube resolver; Kinopoisk unchanged.

## API contracts

### `POST /api/catalog/resolve-by-url`

**Body:** `{ "url": "https://..." }`

**YouTube success (200):**

```json
{
  "provider": "youtube",
  "external_id": "dQw4w9WgXcQ",
  "kind": "video",
  "title": "…",
  "cover_url": "https://i.ytimg.com/vi/…/hqdefault.jpg",
  "summary": "Channel name",
  "catalog_item_id": null,
  "film": null,
  "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "my_card_id": null
}
```

**Errors:**

| Condition | Status | Detail |
|-----------|--------|--------|
| Unknown host | 422 | `unsupported host` |
| YouTube URL without valid video id | 422 | `unsupported youtube url` |
| Video not found (oEmbed 404) | 404 | `catalog item not found` |
| oEmbed / transport failure | 502 | upstream message |

When the user already has a card for the same video, `my_card_id` is populated (duplicate hint before submit).

Kinopoisk responses are unchanged (`kind: 'film'`, `film` embed present).

### `POST /api/cards`

Extended for `provider=youtube`:

- **Required:** `external_id`, `display_title`
- **Optional:** `display_cover_url`, `display_summary`, `source_url` (max 2048)
- **Forbidden:** `film_id`, `catalog_item_id`
- **Duplicate:** second create for same `(user, youtube, external_id)` → **409**

Example payload after resolve:

```json
{
  "provider": "youtube",
  "external_id": "dQw4w9WgXcQ",
  "display_title": "Test Video",
  "display_cover_url": "https://i.ytimg.com/vi/…/hqdefault.jpg",
  "display_summary": "Test Channel",
  "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "genres": [],
  "rating": 8.0,
  "company": "alone",
  "mood_before": "relax",
  "mood_after": "enjoyed",
  "custom_tags": []
}
```

Watchlist create reuses the same provider fields via `watchlistBinding.ts` (`provider=youtube`, `external_id`, `display_*`).

### Persistence

- `CatalogProvider.youtube` on `catalog_item` enum (used in API typing; no catalog row for videos in v1)
- Partial unique index `uq_user_card_user_provider_external_youtube_partial` on `(user_id, provider, external_id)` where `provider='youtube'`
- Migration: `backend/src/migrations/versions/a2b3c4d5e678_user_card_youtube_external_partial.py`

## Frontend flow

### Rated card (`/cards/new`)

1. User pastes YouTube URL in smart field «Название или ссылка».
2. `useResolveCatalogUrl` → `POST /api/catalog/resolve-by-url`.
3. `bindingFromResolveByUrl` maps `kind: 'video'` → `CreationBinding` `{ kind: 'youtube_video', externalId, sourceUrl, display_* , myCardId }`.
4. Scroll form shows topic chip with provider «YouTube», kind «видео» (`CatalogCandidatesList` labels).
5. Submit → `createYoutubeCard` in `cardApi.ts` with `provider=youtube` + resolved fields.
6. Duplicate: `my_card_id` from resolve or 409 on submit → link to existing card.

### Watchlist (`/watchlist/new`)

Same resolve path; `watchlistBinding.ts` builds watchlist payload with `watchlistYoutubeCardId(externalId)` for planned-card lookup.

### Types

- `UserCardProvider` includes `'youtube'` (`profileTypes.ts`)
- `CatalogResolveByUrlResponse.kind`: `'film' | 'video'` (`catalogApi.ts`)

### Copy / UX

- Placeholder mentions Kinopoisk and YouTube links
- Resolve errors mapped in `mapResolveError` for YouTube host hints
- No YouTube rows in mixed catalog search (URL-only in v1)

## Verification

Docker-backed pytest and frontend build (2026-07-19):

| Command | Outcome |
|---------|---------|
| `make backend-test-one target="src/tests/providers/test_youtube_url.py src/tests/providers/test_youtube_oembed_client.py src/tests/services/catalog/test_resolve_youtube_video_by_url_service.py"` | **28 passed** |
| `make backend-test-one target=src/tests/api/test_catalog_routes.py` | **25 passed** |
| `make backend-test-one target="src/tests/api/test_cards_routes.py::test_create_card_youtube_provider_happy_path src/tests/api/test_cards_routes.py::test_create_card_youtube_duplicate_returns_409"` | **2 passed** |
| `cd frontend && npm run lint && npm run build` | **pass** |

**Manual QA:** paste `https://youtu.be/…` on `/cards/new` → resolve prefills form → publish → card detail shows title, thumbnail, and source link. Same on `/watchlist/new`.

## Known limitations

- **URL-only:** no YouTube results in `GET /api/catalog/candidates` text search
- **oEmbed only:** no duration, view count, or rich channel metadata; author name used as summary
- **No catalog row:** videos are not joinable via `catalog_item_id`; profile/stats treat them as abstract cards
- **Single video:** playlist and channel URLs are not supported
- **External dependency:** resolve requires YouTube oEmbed availability; failures surface as 502
- **Feed UI:** video cards use the same card chrome as films/games (no dedicated video player layout)

## v2 follow-ups

- YouTube text search Source in mixed candidates (Data API or alternative index)
- Richer metadata (duration, embed URL, channel id) via YouTube Data API with quota management
- Optional `catalog_item` normalization for cross-user discovery
- Feed/detail UI: inline embed or «open on YouTube» affordance
- Playlist import (multi-card or collection type)
- Offline / cached oEmbed for repeat resolves

## References

- Feature spec: `.cursor/features/youtube-card-source/feature.md`
- Implementation plan: `docs/superpowers/plans/2026-07-19-youtube-card-source.md`
- Delivery result: `.cursor/active/youtube-card-source/result.md`
