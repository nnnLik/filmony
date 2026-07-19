# YouTube Source (URL resolve) Plan

## Feature
- Slug: youtube-card-source
- Status: in_progress
- Spec baseline: [docs/superpowers/specs/2026-07-19-card-post-create-redesign-design.md](../../../docs/superpowers/specs/2026-07-19-card-post-create-redesign-design.md) § Future: YouTube
- Full plan copy: [docs/superpowers/plans/2026-07-19-youtube-card-source.md](../../../docs/superpowers/plans/2026-07-19-youtube-card-source.md)

## Goal

User pastes a YouTube link in the existing smart field (`/cards/new`, `/watchlist/new`) — system prefills title/thumbnail/description and creates an **abstract** card not tied to film/game catalog.

## Architecture

YouTube is a Source for **resolve-by-url only** (not search). Metadata via **YouTube oEmbed** (no API key). Card persists as `UserCard` with `provider=youtube`, `external_id=<videoId>`, `display_*`, `source_url=<canonical URL>`, `catalog_item_id=null`. Candidate/resolve contract extended with `kind: 'video'`.

**Tech stack:** FastAPI service (`build`/`execute`), httpx oEmbed client, pytest in Docker; minimal React type/binding changes.

## Global constraints

- **v1 scope:** URL resolve only (`youtube.com`, `www.youtube.com`, `m.youtube.com`, `youtu.be`). No `GET /api/catalog/candidates` YouTube search.
- Abstract card: no `catalog_item` / `film` for YouTube in v1.
- `POST /api/cards` and watchlist create — validation extension only; no breaking changes for kinopoisk/rawg/manual.
- `kind_hint` / `kind` — UI-only; not a domain card type.
- Docker tests: `make backend-test-one target=…`; frontend: `npm run lint && npm run build`.

## Task sequence

### Task 1 — Delivery scaffolding
Feature slug `youtube-card-source`: `feature.md`, `plan.md`, `progress.md`, action-log entry.

### Task 2 — YouTube URL parsing + oEmbed client (TDD)
- Unit tests: valid/invalid URLs, youtu.be, watch?v=, shorts, embed paths.
- `YoutubeOembedClient.fetch(url)` → title, thumbnail_url, author_name; map 404 → not found.

### Task 3 — `ResolveYoutubeVideoByUrlService`
- `execute(url: str) -> YoutubeVideoDTO` with `video_id`, `canonical_url`, `title`, `cover_url`, `summary`.
- Errors: `UnsupportedUrlError`, `VideoNotFoundError`, `UpstreamError`.

### Task 4 — Extend `resolve-by-url` API
- Refactor `ResolveCatalogByUrlService` to delegate youtube hosts.
- Update `CatalogResolveByUrlResponse`: Kinopoisk unchanged; YouTube returns `provider=youtube`, `kind=video`, `catalog_item_id=null`, `film=null`, `source_url`.
- Route tests: happy youtube URL, invalid host 422, bad video id 404, oEmbed failure 502.

### Task 5 — Card create path for `provider=youtube`
- Add optional `source_url` to `CardCreateRequest`.
- Validator: `provider=youtube` requires `external_id` + `display_title`; forbids `film_id`/`catalog_item_id`.
- `CreateUserCardService`: persist youtube fields; duplicate lookup by user+provider+external_id.
- API tests: create from youtube resolve payload; duplicate behavior.

### Task 6 — Frontend bindings (minimal)
- Extend types; `youtube_video` binding from resolve (no `film` dependency).
- `CreateCardPage` + `WatchlistForm`: resolve + submit with youtube fields + `source_url`.
- UI labels: provider «YouTube», kind «видео»; placeholder/error copy for YouTube links.

### Task 7 — Verification + docs closeout
- `make backend-test-one`; `npm run lint && npm run build`.
- `docs/features/youtube-card-source.md`, `result.md`, action-log.
- Manual QA: paste youtu.be link → preview → publish → card detail.

## Out of scope (v1)

- YouTube text search in candidates
- YouTube Data API v3
- `catalog_item` for videos
- Feed card visual redesign for video
- Playlist/channel import
