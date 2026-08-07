# Progress — film-award-badges

**Status:** in_progress  
**Started:** 2026-08-07

## Log

| When | Action |
|------|--------|
| 2026-08-07T001500Z | Feature request (`.cursor/features/film-award-badges/feature.md`), implementation plan, and progress tracker created. Scope locked to Oscar Best Picture nominee/winner badges on `Film`; Celery external schedule pattern documented. |
| 2026-08-07T221000Z | Slice 5 shipped: `FilmAwardBadge` model + migration `q2r3s4t5u678`, `SyncFilmAwardBadgesService` (curated oscars JSON → kinopoisk_id lookup), `manage_sync_film_award_badges.py` + `make sync-film-award-badges`, Celery task registration, `FilmResponse.award_badges` wired in film/catalog routes, integration idempotency tests, frontend `FilmAwardBadgeStrip` on `FilmDetailPage` + optional `CatalogRatedFilmRow`. |
| 2026-08-07T231900Z | Oscar year UX: merged badge with release year — `OscarReleaseYearLabel`, `filmAwardBadgeDisplay` helpers (release year labels + ceremony in a11y/tooltip), replaced pills/strips on FeedCard, MovieCardDetail, FilmDetail, CatalogRatedFilmRow, CollectionFilmRow; removed `FilmAwardBadgeStrip`. Backend: `award_badges` on `GET /api/collections/{slug}/films`. Verified: `npm run lint && npm run build`, `vitest run filmAwardBadgeDisplay.test.ts`, `make backend-test-one …test_collection_films_include_award_badges`. |
