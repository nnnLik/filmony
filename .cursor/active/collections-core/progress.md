# Progress — collections-core

**Status:** in_progress  
**Started:** 2026-08-07

## Log

| When | Action |
|------|--------|
| 2026-08-07T001500Z | Specs created: `feature.md`, `plan.md`, `progress.md`. |
| 2026-08-07T001800Z | UX spec expanded: BottomNav tab «Коллекции», list + detail screens, flat film rows with rated/unrated visual, infinite scroll pagination, `/films/:filmId` navigation, paginated API with `viewer_has_rated`. Updated `feature.md` FR-6–FR-9 + AC; `plan.md` Phase 5 (films sub-resource) + Phase 7 (concrete frontend paths). |
| 2026-08-07T002000Z | Specs extended: **`content_updated_at`** on `Collection` (catalog changes only; progress/pins excluded); **`UserCollectionPin`** + pin/unpin API (max 10); profile **«Коллекции»** tab always present, empty until ≥1 pin; owner pins + owner progress on public profile; cross-ref **`achievements-rarity-profile-pins`** (achievement pins vs collection pins). Updated `feature.md` FR-10–FR-12 + AC; `plan.md` Phase 1/3/3b/5/7/7b/8 + dependency graph. |

## 2026-08-07T004500Z — Phase 1 models + migration

- **Files:** `backend/src/models/collection.py`, `collection_film.py`, `user_collection_progress.py`, `user_collection_pin.py`, `backend/src/models/__init__.py`, `backend/src/migrations/versions/p1q2r3s4t567_collection_domain.py`
- **Tables:** `collection`, `collection_film`, `user_collection_progress`, `user_collection_pin`
- **Verification:** `docker exec -w /opt/app filmony-backend alembic upgrade head` → success (`o7p8q9r0s123 -> p1q2r3s4t567`); models import OK

## 2026-08-07T010800Z — Phase 2 seed (Letterboxd Top 500)

- **Files:** `backend/src/data/curated/letterboxd_top_500_kinopoisk.json`, `backend/src/manage_seed_letterboxd_top_500.py`, `Makefile` target `seed-letterboxd-top-500`
- **Run:** `docker exec -w /opt/app filmony-backend python src/manage_seed_letterboxd_top_500.py`
- **Summary:** `created_films=292`, `reused_films=208`, `linked=500`, `updated_links=1`, `skipped_todo=0`, `errors=0`
- **Collection:** slug `letterboxd-top-500`, `film_count=499` (500 manifest rows; 1 duplicate kinopoisk_id in mapping)
- **Notes:** TMDB transport unavailable in dev — seed uses Kinopoisk API + optional enrich fallback; idempotent re-run confirmed

## 2026-08-07T010000Z — Prod seed scripts prepared (no local DB seed)

- **Curated data copied to backend:** `backend/src/data/curated/oscars/oscars_{2020..2026}_kinopoisk.json` (67 films)
- **Scripts:** `backend/src/manage_seed_letterboxd_top_500.py` (docstring + prod runbook), `backend/src/manage_seed_oscars.py` (new)
- **Makefile:** `seed-letterboxd-top-500`, `seed-oscars` (`YEAR=` optional), `seed-collections` (both)
- **Runbook:** `.cursor/active/collections-core/PROD_SEED.md`
- **Local DB:** intentionally NOT seeded in this session (no migrate, no seed exec)

## 2026-08-08T021500Z — Catalog sub-tabs: Letterboxd / Оскары

- **Scope:** global `/collections` index only (profile pinned tab unchanged)
- **Files:** `frontend/src/lib/collectionsCatalogSource.ts`, `frontend/src/components/collections/CollectionsSourceTabs.tsx`, `frontend/src/pages/CollectionsIndexPage.tsx`, `frontend/src/lib/__tests__/collectionsCatalogSource.test.ts`
- **Behavior:** `SegmentedControl` in `PageHeader`; Letterboxd → `GET /api/collections?kind=evergreen`, Оскары → `?kind=seasonal`
- **Verification:** `cd frontend && npm run lint && npm run build`; `vitest run src/lib/__tests__/collectionsCatalogSource.test.ts`

## 2026-08-07T011500Z — Slice 1: progress services + card hooks

- **Services:** `services/collections/meaningful_rated_card.py`, `refresh_user_collection_progress.py`, `refresh_progress_for_film.py`, `complete_collection.py`, `__init__.py`
- **Achievement stub:** `services/achievements/grant_collection_achievement.py`
- **Card hooks:** `create_user_card.py`, `update_user_card.py`, `delete_user_card.py`
- **Tests:** unit `tests/unit/services/collections/test_refresh_user_collection_progress.py`; integration `tests/integration/services/collections/test_collection_progress_on_card.py`
- **Celery:** skipped (optional for slice 1)

## 2026-08-07T220800Z — Slice 2: Collections HTTP API

- **Services:** `list_collections.py`, `get_collection.py`, `list_collection_films.py`, `pin_collection.py`, `unpin_collection.py`, `list_profile_pinned_collections.py`
- **API:** `api/collections/schemas.py`, `api/collections/routes.py`; registered in `api/router.py`
- **Auth:** `OptionalUser` in `deps/auth.py` for optional-auth list/detail/films/profile endpoints
- **Endpoints:** `GET /api/collections`, `GET /api/collections/{slug}`, `GET /api/collections/{slug}/films`, `POST/DELETE /api/me/collection-pins/{slug}`, `GET /api/profiles/{user_id}/collections`
## 2026-08-07T221500Z — Slice 4: Profile collections tab + pin/unpin (frontend)

- **Profile tab:** `ProfileMainTabs` third tab «Коллекции»; `ProfileCollectionsPanel` on `ProfilePage` + `PublicProfilePage`
- **API/hooks:** `collectionsApi.ts` pin/unpin + profile pinned list; `useProfilePinnedCollectionsQuery`, `useCollectionPinMutation` (invalidates profile pinned query)
- **Detail pin UX:** `PinCollectionButton` on `CollectionDetailPage` via `CollectionDetailHeader`
- **Components:** `ProfilePinnedCollectionRow`, `CollectionProgressBar`, `CollectionDetailPage` (header + films list)
- **Verification:** `cd frontend && npm run lint && npm run build` — pass


## 2026-08-07T221500Z — Slice 3: Collections discovery frontend

- **API/types:** `frontend/src/api/collectionsTypes.ts`, `frontend/src/api/collectionsApi.ts`
- **Hooks:** `useCollectionsList`, `useCollectionDetail`, `useCollectionFilmsInfinite`
- **Pages:** `CollectionsIndexPage`, `CollectionDetailPage`
- **Components:** `CollectionListItem`, `CollectionDetailHeader`, `CollectionProgressBar`, `CollectionFilmRow`, `CollectionFilmsList`
- **Nav/routes:** 4th BottomNav tab «Коллекции» → `/collections`; AppShell routes; `ScrollToTopFab` whitelist
- **Skipped slice 4:** profile pins tab + `PinCollectionButton` (stub omitted)
- **Verification:** `cd frontend && npm run lint && npm run build` — pass

## 2026-08-07T003000Z — Film card: collections strip

- **API:** `GET /api/films/{film_id}/collections` via `ListFilmCollectionsService`
- **UI:** `FilmCollectionsStrip` under «Друзья оценили» on `MovieCardDetailPage` (horizontal scroll chips)
- **Tests:** `backend/src/tests/integration/api/test_film_collections_routes.py` — pass (`make backend-test-one`)

## 2026-08-08 — Pipeline artifacts moved to `collections/`

- Working tree relocated from `collections-core/data/` → `collections-core/collections/` (`<slug>/intermediate/`, `_tools/`, per-list full JSON).
- Updated pipeline docs: skill, command, rule, reference, `collections/README.md` (run env: host `uv run` + `vars/.env.development.local`; Docker service `backend` for seed/backfill).
