# Result — card-post-create-redesign

**Status:** complete  
**Date:** 2026-07-19

## What was implemented

### Backend
- **`GET /api/catalog/candidates`** — mixed Kinopoisk + RAWG search via `SearchCatalogCandidatesService`; partial results with `meta.degraded_sources`.
- **`POST /api/catalog/resolve-by-url`** — Kinopoisk URL resolve via `ResolveCatalogByUrlService`.
- **`POST /api/cards/covers/upload`** — card cover upload via `UploadUserCardCoverService` (same pattern as feed post image upload).
- **`CatalogCandidateDTO`** — unified candidate contract for API responses.
- Extended catalog schemas and routes; cover upload route on cards API.

### Frontend
- **`CreateActionSheet`** — single feed «Создать» entry with Карточка / Пост / Позже.
- **`CreateCardPage` rewrite** — Screen A smart field + Screen B single scroll form (replaces 4-step wizard).
- **`CreateWatchlistPage`** — dedicated `/watchlist/new` short form.
- **`CardCoverBlock`**, **`CatalogCandidatesList`**, **`RatedCardScrollForm`**, **`WatchlistForm`** — create flow components.
- API clients (`catalogApi`, `cardApi`), hooks (`useCatalogCandidates`, `useResolveCatalogUrl`), bindings (`createCardBinding`, `watchlistBinding`).
- Routes updated; `FilmDetailPage` watchlist deep-link migrated to `/watchlist/new`.
- `FeedComposeSheet` placeholder clarified; `FeedPage` header unified to one create button.

## Changed files

### Backend (modified)
- `backend/src/api/cards/routes.py`
- `backend/src/api/catalog/routes.py`
- `backend/src/api/catalog/schemas.py`
- `backend/src/services/feed_posts/upload_feed_post_image.py`
- `backend/src/tests/api/test_cards_routes.py`
- `backend/src/tests/api/test_catalog_routes.py`
- `backend/src/utils/user_card_media_key.py`

### Backend (new)
- `backend/src/services/cards/upload_user_card_cover.py`
- `backend/src/services/catalog/catalog_candidate_dto.py`
- `backend/src/services/catalog/resolve_catalog_by_url_service.py`
- `backend/src/services/catalog/search_catalog_candidates_service.py`
- `backend/src/tests/services/catalog/test_search_catalog_candidates_service.py`

### Frontend (modified)
- `frontend/src/api/cardApi.ts`
- `frontend/src/api/catalogApi.ts`
- `frontend/src/components/feed/FeedComposeSheet.tsx`
- `frontend/src/components/profile/WatchlistPosterGrid.tsx`
- `frontend/src/pages/CreateCardPage.tsx`
- `frontend/src/pages/FeedPage.tsx`
- `frontend/src/pages/FilmDetailPage.tsx`
- `frontend/src/routes.tsx`

### Frontend (new)
- `frontend/src/components/create/CardCoverBlock.tsx`
- `frontend/src/components/create/CatalogCandidatesList.tsx`
- `frontend/src/components/create/RatedCardScrollForm.tsx`
- `frontend/src/components/create/WatchlistForm.tsx`
- `frontend/src/components/feed/CreateActionSheet.tsx`
- `frontend/src/hooks/useCatalogCandidates.ts`
- `frontend/src/hooks/useResolveCatalogUrl.ts`
- `frontend/src/lib/createCardBinding.ts`
- `frontend/src/lib/watchlistBinding.ts`
- `frontend/src/pages/CreateWatchlistPage.tsx`

### Docs / delivery
- `docs/features/card-post-create-redesign.md`
- `docs/superpowers/plans/2026-07-19-card-post-create-redesign.md`
- `.cursor/features/card-post-create-redesign/feature.md`
- `.cursor/active/card-post-create-redesign/plan.md`
- `.cursor/active/card-post-create-redesign/progress.md`
- `.cursor/active/card-post-create-redesign/result.md`

## Verification

### Frontend — pass
```bash
cd frontend && npm run lint && npm run build
```
- ESLint: no errors.
- Vite build: success (CreateCardPage, CreateWatchlistPage, FeedPage chunks emitted).

### Backend — environment issue at closeout
```bash
make backend-test-one target=src/tests/api/test_catalog_routes.py
make backend-test-one target=src/tests/api/test_cards_routes.py
```

Both runs hit `UndefinedTableError: relation "user" does not exist` during test DB setup/teardown — indicates migrations not applied in the test container, not feature code regressions. New feature tests added:

**Catalog (`test_catalog_routes.py`):**
- `test_catalog_candidates_mixed_sources`
- `test_catalog_candidates_query_too_short_returns_empty`
- `test_catalog_candidates_one_source_degraded`
- `test_catalog_candidates_same_title_film_and_game_both_returned`
- `test_catalog_resolve_by_url_kinopoisk_happy_path`
- `test_catalog_resolve_by_url_unknown_host_returns_422`
- `test_catalog_resolve_by_url_not_found_returns_404`

**Cards (`test_cards_routes.py`):**
- `test_user_card_cover_upload_requires_auth`
- `test_user_card_cover_upload_success`
- `test_user_card_cover_upload_rejects_bad_type`

**Service unit:**
- `backend/src/tests/services/catalog/test_search_catalog_candidates_service.py`

Re-run after `make start` / migrate test DB:
```bash
make backend-test-one target=src/tests/api/test_catalog_routes.py
make backend-test-one target=src/tests/api/test_cards_routes.py
```

## Known limitations

- YouTube and other Sources deferred; only Kinopoisk + RAWG in candidates.
- Legacy `POST /api/catalog/resolve` retained; new UI uses `resolve-by-url` only.
- No localStorage draft persistence in v1.
- Profile FAB create entry unchanged.

## Next steps

- Apply migrations and confirm backend test suite green in Docker.
- Manual QA: Castlevania mixed candidates, cover upload/link/buffer, watchlist from sheet.
