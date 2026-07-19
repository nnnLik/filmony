# YouTube card source

## Scope

Add YouTube as a **Source** for the existing card create flow: paste a `youtube.com` / `youtu.be` link in the smart field on `/cards/new` or `/watchlist/new` → resolve-by-url → prefill title/thumbnail/description → create an **abstract** `UserCard` with `provider=youtube`, `kind=video`, no `catalog_item`.

**v1 delivery goals:**

- **URL resolve only** for YouTube hosts (`youtube.com`, `www.youtube.com`, `m.youtube.com`, `youtu.be`) — no text search in mixed candidates.
- **Metadata via YouTube oEmbed** (no YouTube Data API / API key).
- **Abstract card persistence:** `provider=youtube`, `external_id=<videoId>`, `display_*`, `source_url`, `catalog_item_id=null`.
- Extend resolve response with `kind: 'video'` alongside existing Kinopoisk `kind: 'film'`.
- Duplicate warning by `(user_id, provider=youtube, external_id)` like Kinopoisk.

**In scope:**

- Backend: YouTube URL parser, oEmbed client, `ResolveYoutubeVideoByUrlService`, extend `POST /api/catalog/resolve-by-url`, extend `POST /api/cards` for `provider=youtube` + `source_url`.
- Frontend: types, `createCardBinding` / watchlist bindings, `CreateCardPage` + `WatchlistForm` resolve + submit paths, provider/kind labels.

**Non-goals (v1):**

- YouTube text search in `GET /api/catalog/candidates`.
- YouTube Data API v3 / quota management.
- `catalog_item` row for videos.
- Feed card visual redesign for video cards.
- Playlist/channel import.

**Spec baseline:** `docs/superpowers/specs/2026-07-19-card-post-create-redesign-design.md` § Future: YouTube.

## Acceptance Criteria

### Backend (pytest inside Docker)

- YouTube URL parser: valid watch, youtu.be, shorts, embed; invalid → error.
- oEmbed client: happy path title/thumbnail; 404 → not found; upstream failure → 502.
- `POST /api/catalog/resolve-by-url`: YouTube URL → `provider=youtube`, `kind=video`, `external_id`, `source_url`, `catalog_item_id=null`, `film=null`.
- Unknown host still → 422; bad video id → 404.
- `POST /api/cards` with `provider=youtube`: requires `external_id` + `display_title`; forbids `film_id`/`catalog_item_id`; persists `source_url`.
- Duplicate `(user, youtube, videoId)` returns existing-card warning behavior.

### Frontend

- `cd frontend && npm run lint && npm run build` — zero errors in touched files.
- Paste `https://youtu.be/…` on `/cards/new` → resolve → scroll form prefilled → publish → card detail shows title + thumbnail + link.
- Same resolve flow on `/watchlist/new`.
- Provider badge «YouTube», kind «видео»; smart field placeholder/error copy mentions YouTube links.
