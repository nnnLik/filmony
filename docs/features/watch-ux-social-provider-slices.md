# Watch UX, social slices, and provider catalog (P0–P2)

Product slices from the provider-backed film ideas plan: watch-room leave flow, TMA→browser same party, honest playback errors, visible friend ratings on cards, watchlist overlap + evening-for-two, watching-now vitrine, and KP/TMDB passport metadata on film detail.

## P0 — Leave watch room → rate prompt

When leaving `/films/:id/watch` (header back, TMA BackButton, browser `popstate`, tab hide best-effort):

- **Оценить фильм** → leave party quietly, navigate to `/cards/new?filmId=` or `/cards/{my_card_id}/edit`
- **Не оценивать** → leave and return to `/films/:id`

Implementation: `frontend/src/lib/watchLeaveRatePrompt.ts`, `WatchLeaveRateSheet.tsx`, wired in `FilmWatchPage.tsx`.

Tests: `frontend/src/lib/__tests__/watchLeaveRatePrompt.test.ts`.

## P0 — TMA «Смотреть» → same browser party

Before `openLink`, TMA creates a watch party and opens `/films/{id}/watch?party={invite_slug}`. On create failure, opens watch URL without party (previous behavior).

Implementation: `frontend/src/lib/openFilmWatchInBrowser.ts` (`openFilmWatchInBrowserAfterParty`).

Tests: `frontend/src/lib/__tests__/openFilmWatchInBrowser.test.ts`.

## P1 — Playback unavailable

- Backend maps empty pleer embed to **422** `playback_unavailable` (`pleer_video_client.py`, `resolve_film_playback.py`).
- Watch page shows `PlaybackUnavailableState` and skips `useEnsureWatchParty` until playback succeeds with non-empty iframe.

Tests: `backend/src/tests/unit/providers/playback/test_pleer_video_client.py`, `backend/src/tests/integration/api/test_film_playback_routes.py`.

## P1 — Friend ratings on movie cards

On KP/film `MovieCardDetailPage`: compact `FollowingRatingsPanel` above the note, `communityLink` → `/films/{filmId}`.

## P2 — «Оба хотите» + «Вечер на двoих»

- Profile overlap block title **«Оба хотите посмотреть»** (`WatchlistOverlapSection`).
- `GET /api/me/watchlist/evening-for-two?partner_user_id=` picks one shared watchlist film neither user has rated.
- UI: `EveningForTwoSection.tsx` on profile watchlist panel.

Tests: `backend/src/tests/integration/api/test_evening_for_two_routes.py`.

## P2 — «Сейчас смотрят» vitrine

- `GET /api/watch-parties/watching/following` lists following users in live parties.
- `WatchingNowVitrineSection.tsx` on profile page.

Tests: covered by watch-party integration suite where applicable.

## Provider catalog (passport, trailer, similars, where-to-watch)

**Persisted on `film` (migrations `h6i7j8k9l012` sidecar → `i7j8k9l0m123` columns):** Kinopoisk passport fields. Prod DB objects owned by app role `filmony`.

**TMDB snapshot append:** `videos,recommendations,watch/providers` in `tmdb_provider_transport.py`.

**API (`FilmResponse`):** passport fields, `tmdb_recommendations` (titles), `trailer_youtube_url`, `watch_providers_ru`.

**UI (`FilmDetailPage`):** slogan, `FilmPassportRow`, `FilmSimilarTitles`, `FilmTrailerLink`, `FilmWatchProvidersRow`.

Tests: `backend/src/tests/unit/api/films/test_film_passport_mapper.py`, `backend/src/tests/unit/providers/tmdb/*`, `frontend/src/lib/__tests__/filmPassportDisplay.test.ts`.

## Verification

```bash
make migrate   # applies h6i7j8k9l012 if needed
make backend-test-one target=src/tests/integration/api/test_evening_for_two_routes.py
make backend-test-one target=src/tests/integration/api/test_film_playback_routes.py
make backend-test-one target=src/tests/unit/providers/tmdb/
cd frontend && npm run lint && npm run build && npm run test -- --run src/lib/__tests__/
```

## Out of scope (already in prod)

Telegram push on card reactions — `notify_reaction_added` Celery task; no duplicate work.

## Follow-ups

- KP premieres/tops browse, facts/images/awards (quota-aware lazy load).
- Link TMDB recommendation titles to in-app film pages when matched.
