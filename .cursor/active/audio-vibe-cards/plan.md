# Plan: audio-vibe-cards

1. **Migration + model** — Add nullable `audio_url`, `audio_repeat_enabled` (default false), `audio_repeat_delay_ms` (default 0) on user card table.
2. **Storage + services** — RustFS prefix for card audio; `UploadUserCardAudioService`, attach flow, `DeleteUserCardAudioService`; reuse/delete old object on replace/remove; `rustfs_delete_object` helper; `user_card_media_key` for proxy URL + safety.
3. **Read paths** — Thread fields through `GetUserCardDetails`, `ListUserCardFeed`, `ListUserCards`; schemas for feed/profile/cards.
4. **Write paths** — `UpdateUserCard` accepts repeat fields with delay bounds; routes `POST/DELETE .../audio`, `GET .../media/{key}`.
5. **Tests** — Extend `test_cards_routes.py` (happy path, 403, bad MIME, oversize, delete, PATCH repeat, unsafe media path).
6. **Frontend** — `profileTypes`, `cardApi` upload/delete + PATCH payload; `movieCardAudioMedia` URL helper; `MovieCardAudioPlayer`; `MovieCardDetailPage`; owner section on `EditMovieCardPage`.
7. **Feed global audio (add-on)** — `FeedCardGlobalAudioProvider` on **FeedPage** owns a single hidden `<audio>`; `FeedCard` uses context so playback survives list scroll/virtualization; leaving the feed route or disabling audio in FAB pauses playback; `FeedTopFab` gains volume toggle stacked above scroll/reload FAB; preference `filmony-feed-card-audio-enabled` in `localStorage`.
8. **Verification** — `pytest tests/api/test_cards_routes.py` in backend container; `npm run lint && npm run build` in `frontend/`.
9. **Docs + logs** — `docs/features/audio-vibe-cards.md`, action-log fragment, `result.md` when done.
