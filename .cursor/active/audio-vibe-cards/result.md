# Result: audio-vibe-cards

## Implemented
- Optional per-card audio stored in RustFS; DB stores API-relative `audio_url` plus `audio_repeat_enabled` / `audio_repeat_delay_ms` (0–60000 ms on PATCH).
- `POST /api/cards/{card_id}/audio` and `DELETE /api/cards/{card_id}/audio` (owner-only); `GET /api/cards/media/{media_key:path}` proxies RustFS for browser `<audio>` / download without Authorization header.
- Allowed MIME: `audio/mpeg`, `audio/mp4`, `audio/ogg`, `audio/wav`, `audio/webm`; max size **20 MiB** server-side.
- Card detail page: audio player with autoplay-muted attempt, controls, repeat-with-delay behavior from API fields, download.
- Edit page (owner): upload/replace/remove audio; repeat toggle and delay saved with main Save (PATCH).

## Changed / added files (main)
- **Backend:** `backend/src/migrations/versions/b5c6d7e8f901_movie_card_audio_vibe.py`, `backend/src/models/user_card.py`, `backend/src/utils/user_card_media_key.py`, `backend/src/utils/rustfs_delete_object.py`, `backend/src/services/cards/upload_user_card_audio.py`, `attach_user_card_audio.py`, `delete_user_card_audio.py`, `update_user_card.py`, `get_user_card_details.py`, `list_user_card_feed.py`, `backend/src/services/profile/list_user_cards.py`, `backend/src/api/cards/routes.py`, `backend/src/api/cards/schemas.py`, `backend/src/api/feed/routes.py`, `backend/src/api/profile/schemas.py`, `backend/src/tests/api/test_cards_routes.py`
- **Frontend:** `frontend/src/lib/movieCardAudioMedia.ts`, `frontend/src/components/cards/MovieCardAudioPlayer.tsx`, `frontend/src/api/profileTypes.ts`, `frontend/src/api/cardApi.ts`, `frontend/src/pages/MovieCardDetailPage.tsx`, `frontend/src/pages/EditMovieCardPage.tsx`

## Verification
| Check | Command | Outcome |
|-------|---------|---------|
| Frontend lint | `cd frontend && npm run lint` | OK |
| Frontend build | `cd frontend && npm run build` | OK |
| Cards API tests (Docker) | `docker exec -w /opt/app/src filmony-backend pytest tests/api/test_cards_routes.py -q` | **63 passed** |
| Full backend suite | `docker exec -w /opt/app/src filmony-backend pytest` | **283 passed, 2 failed** — failures in `test_feed_post_only_mention_follower_skips_follower_broadcast` and `test_lists_distinct_followers_in_stable_order` (unrelated to this feature; pre-existing/flaky) |

**Note:** `make backend-test` uses `docker exec -it` and fails in non-TTY environments; use `docker exec -w /opt/app/src filmony-backend pytest …` without `-t` for CI-like runs.

## Limitations / follow-ups
- Audio attach UI only on edit flow (by design for v1).
- Full suite green depends on fixing or stabilizing the two unrelated failing tests above.
