---
name: audio-vibe-cards
overview: Add a single optional audio layer to any user card. The first version keeps the upload flow on the edit screen, plays audio from the card detail page, and supports a simple repeat-with-delay mode for voice notes or ambience.
todos:
  - id: backend-model-and-api
    content: Add audio columns, services, routes, and API coverage for card audio upload/delete and proxy media serving.
    status: completed
  - id: frontend-player-and-editor
    content: Add the audio player to card detail and the upload/remove controls to the edit page, wired through `cardApi` and shared types.
    status: completed
  - id: verification
    content: Run backend tests plus frontend lint/build and record the result in the feature delivery artifacts.
    status: completed
isProject: false
---

# Audio vibe cards

## Scope
- Add one optional audio asset per `UserCard` that works for any card type, not just music.
- Keep the MVP simple: users attach audio from the existing card edit flow, while the card detail page handles playback.
- Do **not** add audio to the create-card wizard in v1.

## Backend plan
- Extend the card model in [`backend/src/models/user_card.py`](backend/src/models/user_card.py) with:
  - `audio_url` (`nullable` string)
  - `audio_repeat_enabled` (`bool`, default `false`)
  - `audio_repeat_delay_ms` (`int`, default `0`)
- Add a migration for the new columns and default values.
- Thread the new fields through the shared card payloads returned by:
  - [`backend/src/services/cards/get_user_card_details.py`](backend/src/services/cards/get_user_card_details.py)
  - [`backend/src/services/cards/list_user_card_feed.py`](backend/src/services/cards/list_user_card_feed.py)
  - [`backend/src/services/profile/list_user_cards.py`](backend/src/services/profile/list_user_cards.py)
- Add a dedicated upload/delete flow for card audio:
  - `POST /api/cards/{card_id}/audio` uploads/replaces the file.
  - `DELETE /api/cards/{card_id}/audio` removes it.
  - `GET /api/cards/media/{media_key:path}` proxies RustFS content so `<audio>` and download links work without Bearer headers.
- Keep the route thin in [`backend/src/api/cards/routes.py`](backend/src/api/cards/routes.py); move storage logic into new services such as `UploadUserCardAudioService` and `DeleteUserCardAudioService`.
- Validate:
  - ownership before write/delete,
  - allowed audio mime types only (`audio/mpeg`, `audio/mp4`, `audio/ogg`, `audio/wav`, `audio/webm`),
  - a sensible max size (choose one fixed limit and enforce it server-side),
  - one audio file per card, replacing the previous one on upload.
- Store files in RustFS under a dedicated prefix like `user_media/movie_card_audio/...` and delete the old object when replacing/removing audio.

## Frontend plan
- Add audio fields to [`frontend/src/api/profileTypes.ts`](frontend/src/api/profileTypes.ts) and upload/delete helpers in [`frontend/src/api/cardApi.ts`](frontend/src/api/cardApi.ts).
- Create a small reusable player component, e.g. [`frontend/src/components/cards/MovieCardAudioPlayer.tsx`](frontend/src/components/cards/MovieCardAudioPlayer.tsx), instead of embedding audio logic directly in the page.
- Show the player on [`frontend/src/pages/MovieCardDetailPage.tsx`](frontend/src/pages/MovieCardDetailPage.tsx):
  - attempt autoplay muted on open,
  - fall back to an explicit play control if the browser blocks autoplay,
  - provide mute/unmute, pause/play, loop toggle, and download.
- Add an owner-only audio section to [`frontend/src/pages/EditMovieCardPage.tsx`](frontend/src/pages/EditMovieCardPage.tsx): upload/replace file, toggle repeat, set repeat delay, and remove audio.
- Add a small helper for building the media proxy URL, similar to the existing comment image helper pattern, so the detail page and download button use the same path.

## Tests and verification
- Extend [`backend/src/tests/api/test_cards_routes.py`](backend/src/tests/api/test_cards_routes.py) with coverage for:
  - successful audio upload,
  - forbidden upload/delete by non-owner,
  - invalid mime type / oversized file,
  - delete behavior,
  - audio fields present in card detail responses.
- Add focused service tests if needed for the audio upload/delete service logic.
- For frontend, keep the change lightweight and verify manually if there is no existing component-test harness for this area.
- Final verification after implementation should include backend tests in Docker plus frontend lint/build.
