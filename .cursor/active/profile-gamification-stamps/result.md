# Result: profile-gamification-stamps

Status: **done**

## Implemented

### Shared infra
- `Film` model: `countries`, `primary_director_kinopoisk_id`, `primary_director_name`, `franchise_key` + Alembic migration.
- Kinopoisk integration: `GET /v1/staff?filmId=`, `GET /v2.1/films/{id}/sequels_and_prequels`; staff/sequels DTOs; lazy enrich on resolve + `manage_backfill_film_gamification_metadata.py` (`make backfill-film-gamification-metadata`).
- Community stats: `GetCatalogCommunityStatsService` → `community_avg_rating`, `is_contrarian` (delta ≥ 4.0, `ratings_count >= 3`) in card list/detail DTOs.
- Gamification API: `GET /api/me/gamification` (passport, marathons, shelf_physics); `GET /api/users/{id}/gamification/passport` (public read-only unlocked stamps).

### Ф13 — Кино-паспорт
- `ComputePassportStampsService` + stamp catalog (`passport_stamps.py` / TS mirror).
- Rules: first country, first rating of decade, 5+ countries in calendar year, N unique countries (5/10/20), meta-stamp «первая оценка в году».
- `ProfilePassportPanel` + sub-tab **«Коллекция»** in Stats; locked/unlocked + progress; public profile shows unlocked stamps only.

### Ф14 — Бейдж «контр-культ»
- `is_contrarian` on own card list/detail API paths.
- `ContrarianBadge` on own cards: profile grid, card detail, own FeedCard; hidden when `ratings_count < 3`.

### Ф15 — Режиссёрский / франшизный марафон
- `ComputeMarathonAchievementsService`: director or franchise with 5+ rated film-backed cards.
- `MarathonShelfFrame` + achievement chips in passport panel; drill-down via title search filter.

### Ф16 — Полка-физика
- `ComputeShelfPhysicsService` + `ProfileShelfPhysics` wrapper on own ProfilePage rated grid.
- States: `neutral` / `slump` (3+ consecutive ≤3) / `glow` (3+ consecutive ≥9).
- `prefers-reduced-motion` → static tint, no animation.

### Ф17 — Pepe-судья
- Frontend-only: random Pepe phrase when rating crosses **1** or **10** in create/edit rated card flow.
- Debounced threshold crossing; no spam on drag.

## Changed files

### Backend
- `Makefile`
- `backend/src/api/cards/routes.py`
- `backend/src/api/cards/schemas.py`
- `backend/src/api/gamification/routes.py`
- `backend/src/api/gamification/schemas.py`
- `backend/src/api/profile/schemas.py`
- `backend/src/api/profile/users_routes.py`
- `backend/src/api/router.py`
- `backend/src/const/passport_stamps.py`
- `backend/src/manage_backfill_film_gamification_metadata.py`
- `backend/src/migrations/versions/g2h3i4j5k678_film_gamification_metadata.py`
- `backend/src/models/film.py`
- `backend/src/providers/kinopoisk/__init__.py`
- `backend/src/providers/kinopoisk/kinopoisk_provider_transport.py`
- `backend/src/providers/kinopoisk/kinopoisk_search_dto.py`
- `backend/src/providers/kinopoisk/kinopoisk_sequels_dto.py`
- `backend/src/providers/kinopoisk/kinopoisk_staff_dto.py`
- `backend/src/services/catalog/batch_catalog_community_stats.py`
- `backend/src/services/catalog/card_community_fields.py`
- `backend/src/services/catalog/community_stats_dto.py`
- `backend/src/services/catalog/get_catalog_community_stats.py`
- `backend/src/services/catalog/search_kinopoisk_films_local_first.py`
- `backend/src/services/gamification/__init__.py`
- `backend/src/services/gamification/compute_marathon_achievements.py`
- `backend/src/services/gamification/compute_passport_stamps.py`
- `backend/src/services/gamification/compute_shelf_physics.py`
- `backend/src/services/gamification/enrich_film_gamification_metadata.py`
- `backend/src/services/kinopoisk/client.py`
- `backend/src/services/kinopoisk/resolve_kinopoisk_film.py`
- `backend/src/tests/api/test_cards_routes.py`
- `backend/src/tests/api/test_catalog_routes.py`
- `backend/src/tests/api/test_gamification_routes.py`
- `backend/src/tests/providers/test_kinopoisk_gamification_dtos.py`
- `backend/src/tests/services/gamification/test_enrich_film_gamification_metadata.py`

### Frontend
- `frontend/src/api/gamificationApi.ts`
- `frontend/src/api/gamificationTypes.ts`
- `frontend/src/api/profileTypes.ts`
- `frontend/src/components/create/RatedCardScrollForm.tsx`
- `frontend/src/components/feed/FeedCard.tsx`
- `frontend/src/components/gamification/ContrarianBadge.tsx`
- `frontend/src/components/profile/MoviePosterGrid.tsx`
- `frontend/src/components/profile/ProfileStatsPanel.tsx`
- `frontend/src/components/profile/gamification/MarathonShelfFrame.tsx`
- `frontend/src/components/profile/gamification/ProfilePassportPanel.tsx`
- `frontend/src/components/profile/gamification/ProfileShelfPhysics.tsx`
- `frontend/src/components/profile/gamification/profileShelfPhysics.css`
- `frontend/src/components/ui/PepeExtremeRatingBubble.tsx`
- `frontend/src/hooks/useGamification.ts`
- `frontend/src/hooks/usePepeExtremeRatingJudge.ts`
- `frontend/src/lib/gamification/gamificationQueryKeys.ts`
- `frontend/src/lib/gamification/passportStamps.ts`
- `frontend/src/lib/gamification/shelfPhysicsFallback.ts`
- `frontend/src/lib/microFun/microFunCopy.ts`
- `frontend/src/pages/EditMovieCardPage.tsx`
- `frontend/src/pages/MovieCardDetailPage.tsx`
- `frontend/src/pages/ProfilePage.tsx`
- `frontend/src/pages/PublicProfilePage.tsx`

## Verification

```bash
make backend-test-one target=src/tests/api/test_gamification_routes.py
# 11 passed

make backend-test-one target=src/tests/providers/test_kinopoisk_gamification_dtos.py src/tests/services/gamification/test_enrich_film_gamification_metadata.py
# 7 passed

cd frontend && npm run lint && npm run build
# passed
```

## Known limitations

- **Film-only:** passport stamps and marathons apply only to **film-backed rated cards** (inner join `Film`); games, manual cards, and planned cards are excluded.
- **Backfill required:** existing films need `make backfill-film-gamification-metadata` (or re-resolve via Kinopoisk) to populate `countries`, director, and franchise metadata before stamps/marathons unlock retroactively.
- **Marathon drill-down:** achievement chips filter the rated grid via **title search**, not a dedicated marathon filter endpoint.
- **v2 deferred:** «первая ч/б» stamp not in v1 (no reliable B&W metadata from Kinopoisk).
