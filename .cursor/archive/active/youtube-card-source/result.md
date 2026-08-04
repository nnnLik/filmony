# YouTube card source — Result

## Status

**done** — v1 URL-resolve YouTube Source shipped with backend services, API extensions, frontend bindings, and automated verification.

## What was implemented

- **YouTube URL parser** — watch, youtu.be, shorts, embed; host detection for `youtube.com` / `youtu.be`
- **oEmbed client** — public metadata (title, thumbnail, author) without API key
- **`ResolveYoutubeVideoByUrlService`** — orchestrates parse + oEmbed → `YoutubeVideoDTO`
- **`ResolveCatalogByUrlService`** — routes YouTube hosts to YouTube resolver; Kinopoisk unchanged
- **`POST /api/catalog/resolve-by-url`** — returns `provider=youtube`, `kind=video`, `source_url`, optional `my_card_id`
- **`POST /api/cards`** — `provider=youtube` validation, `source_url`, abstract persistence, duplicate 409
- **DB** — partial unique index on `(user_id, provider, external_id)` for YouTube cards
- **Frontend** — `youtube_video` binding, create/watchlist submit paths, provider/kind labels, smart-field copy

## Changed files

### Backend

- `backend/src/providers/youtube/__init__.py`
- `backend/src/providers/youtube/youtube_url.py`
- `backend/src/providers/youtube/youtube_oembed_client.py`
- `backend/src/services/catalog/youtube_video_dto.py`
- `backend/src/services/catalog/resolve_youtube_video_by_url_service.py`
- `backend/src/services/catalog/resolve_catalog_by_url_service.py`
- `backend/src/api/catalog/routes.py`
- `backend/src/api/catalog/schemas.py`
- `backend/src/api/cards/schemas.py`
- `backend/src/services/cards/create_user_card.py`
- `backend/src/models/catalog_item.py`
- `backend/src/migrations/versions/a2b3c4d5e678_user_card_youtube_external_partial.py`
- `backend/src/tests/providers/test_youtube_url.py`
- `backend/src/tests/providers/test_youtube_oembed_client.py`
- `backend/src/tests/services/catalog/test_resolve_youtube_video_by_url_service.py`
- `backend/src/tests/api/test_catalog_routes.py`
- `backend/src/tests/api/test_cards_routes.py`

### Frontend

- `frontend/src/api/profileTypes.ts`
- `frontend/src/api/catalogApi.ts`
- `frontend/src/api/cardApi.ts`
- `frontend/src/lib/createCardBinding.ts`
- `frontend/src/lib/watchlistBinding.ts`
- `frontend/src/pages/CreateCardPage.tsx`
- `frontend/src/components/create/WatchlistForm.tsx`
- `frontend/src/components/create/CatalogCandidatesList.tsx`

### Docs / delivery

- `docs/features/youtube-card-source.md`
- `.cursor/active/youtube-card-source/plan.md`
- `.cursor/active/youtube-card-source/progress.md`
- `.cursor/active/youtube-card-source/result.md`
- `.cursor/memory/logs/2026-07-19T164500Z-youtube-card-source-code.md`
- `.cursor/memory/logs/action-log.md`

## Verification

| Command | Outcome |
|---------|---------|
| `make backend-test-one target="src/tests/providers/test_youtube_url.py src/tests/providers/test_youtube_oembed_client.py src/tests/services/catalog/test_resolve_youtube_video_by_url_service.py"` | **28 passed** |
| `make backend-test-one target=src/tests/api/test_catalog_routes.py` | **25 passed** |
| `make backend-test-one target="src/tests/api/test_cards_routes.py::test_create_card_youtube_provider_happy_path src/tests/api/test_cards_routes.py::test_create_card_youtube_duplicate_returns_409"` | **2 passed** |
| `cd frontend && npm run lint && npm run build` | **pass** |

## Known limitations

- URL resolve only — no YouTube text search in mixed candidates
- oEmbed metadata only (no duration/views; author as summary)
- No `catalog_item` row for videos
- Playlist/channel URLs unsupported
- Feed card UI not redesigned for video layout
- Resolve depends on YouTube oEmbed uptime (502 on upstream failure)

## Next steps (v2)

- YouTube search Source in candidates
- YouTube Data API for richer metadata
- Feed/detail embed or dedicated video chrome
- Playlist import
