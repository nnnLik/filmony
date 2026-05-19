# Audio vibe cards

## Summary
Users can attach **one optional audio file** to any movie/user card. Audio is managed on **create** (wizard step 4) and **edit**; the **card detail** page shows a **floating play/pause** control when a track exists (playback via proxied URL, no Bearer on `<audio src>`). There is **no repeat** and **no user-configurable delay**; a single client-side constant controls optional delay before play after tapping play.

## Backend
- **Columns:** `audio_url` (nullable). Legacy columns `audio_repeat_*` were removed in migration `c9d0e1f2a345_drop_movie_card_audio_repeat`.
- **Endpoints**
  - `POST /api/cards/{card_id}/audio` — multipart upload; replaces existing audio; deletes previous RustFS object when present.
  - `DELETE /api/cards/{card_id}/audio` — clears `audio_url` and deletes object.
  - `GET /api/cards/media/{media_key:path}` — proxies RustFS for validated keys.
- **Validation:** MIME whitelist (`audio/mpeg`, `audio/mp4`, `audio/ogg`, `audio/wav`, `audio/webm`); max **50 MiB** server-side; owner-only writes.

## Frontend
- Types: `audio_url` on card types; `MOVIE_CARD_AUDIO_PLAY_START_DELAY_MS` in `frontend/src/lib/movieCardAudioMedia.ts` (default `0`).
- `MovieCardAudioPlayer` — fixed FAB play/pause, portals to `document.body`.
- `CreateCardPage` step 4 — optional file; uploaded immediately after successful `POST /api/cards`. On upload failure, navigates to `/cards/{id}/edit` so the user can retry.

## Testing
- `backend/src/tests/api/test_cards_routes.py` — audio upload/delete/forbidden/MIME/oversize/detail `audio_url`.
