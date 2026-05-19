# Audio vibe cards

## Scope
- One optional audio asset per user card (any card type), attached from the **edit** flow only in v1 (not create wizard).
- Card **detail** shows playback with autoplay-muted attempt, explicit controls, loop + delay honoring server fields, download.
- **API**: upload/replace/delete audio; proxy `GET /api/cards/media/{key}` for `<audio src>` without Bearer; PATCH for repeat settings.

## Acceptance criteria
- [x] DB columns + migration: `audio_url`, `audio_repeat_enabled`, `audio_repeat_delay_ms`.
- [x] Card payloads (detail, feed, profile lists) include audio fields.
- [x] `POST/DELETE /api/cards/{id}/audio` with owner checks, MIME whitelist, 20 MiB max, replace deletes old object.
- [x] Media proxy with path safety checks.
- [x] Frontend: types + `cardApi` helpers, `MovieCardAudioPlayer`, detail + edit owner UI.
- [x] Backend tests for upload/delete/forbidden/validation/proxy/detail; frontend `npm run lint` + `npm run build`.
