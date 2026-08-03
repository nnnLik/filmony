# Progress: profile-gamification-stamps

Status: **done**

## 2026-08-04

### Planning
- Созданы delivery artifacts: `feature.md`, `plan.md`, `progress.md`.
- Источник детального плана: `.cursor/plans/profile_gamification_stamps_f5dfee63.plan.md`.

### Implementation (phases 0–5)
- **v1.1 (2026-08-04):** Director/franchise card filters; `GET /api/users/{id}/rated-directors`; 9 new passport stamp types; collection grouped by category; marathon drill-down uses director/franchise filters.
- **Infra:** Film gamification metadata migration (`countries`, `primary_director_*`, `franchise_key`); Kinopoisk staff/sequels DTOs + transport; `EnrichFilmGamificationMetadataService` + backfill script (`make backfill-film-gamification-metadata`); community stats (`GetCatalogCommunityStatsService`, `is_contrarian` on card DTOs); `GET /api/me/gamification` + public passport endpoint.
- **Ф17 Pepe-судья:** pools `extreme_rating_low/high` в `microFunCopy.ts`, hook `usePepeExtremeRatingJudge`, bubble в create/edit rated card flow; debounce на пересечении порога.
- **Ф16 Полка-физика:** `ComputeShelfPhysicsService` + `ProfileShelfPhysics` wrapper (neutral / slump / glow) на own ProfilePage rated grid; `prefers-reduced-motion` → статичный tint.
- **Ф14 Контр-культ:** `ContrarianBadge` на own cards (grid, detail, FeedCard) при `is_contrarian` (delta ≥ 4.0, count ≥ 3).
- **Ф13 Кино-паспорт:** `ComputePassportStampsService`, stamp catalog, `ProfilePassportPanel` + sub-tab «Коллекция» в Stats; locked/unlocked + progress; public read-only passport на чужом профиле.
- **Ф15 Марафоны:** `ComputeMarathonAchievementsService` (director/franchise, count ≥ 5), `MarathonShelfFrame` + chips с drill-down фильтром.

### Verification
- Backend: `test_gamification_routes.py` — 11 passed; gamification/enrich tests — 7 passed.
- Frontend: `npm run lint && npm run build` — passed.

### Closeout
- `result.md`, `docs/features/profile-gamification-stamps.md`, action-log entry added.
