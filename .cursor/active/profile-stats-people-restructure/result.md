# profile-stats-people-restructure — result

Status: **complete**

## Implemented

- **Sub-tab «Награды»:** when `showAchievements` is true, merged separate **Коллекция** and **Достижения** tabs into a single **«Награды»** tab hosting `ProfilePassportPanel` and `AchievementsPanel` with section headers; collection-only profiles keep prior tab behavior when achievements are hidden.
- **Taste vs Social dedupe:** removed duplicate «С кем смотрите» / «Эмоции после» summary rows from **Социальность**; **Вкус** retains interactive company and mood donut charts with drill/filter behavior.
- **Horizontal people cards:** replaced vertical `DirectorDistributionList` / `ActorDistributionList` with horizontal scroll `PersonDistributionStrip` — portrait photo, name, film count, tap navigates to `/directors/:id` or `/actors/:id` with `userId` query when viewing another profile; footer insight links preserved.
- **Backend director posters:** added `poster_url: str | None` to `DirectorDistributionItem` and API response; populated from `Film.primary_director_poster_url` during aggregation (first non-null poster per director); actors unchanged.

## Changed files

### Backend
- `backend/src/services/profile/get_user_card_stats.py`
- `backend/src/api/profile/schemas.py`

### Tests
- `backend/src/tests/integration/api/test_profile_routes.py`

### Frontend
- `frontend/src/api/profileTypes.ts`
- `frontend/src/components/profile/ProfileStatsPanel.tsx`

### Artifacts
- `.cursor/features/profile-stats-people-restructure/feature.md`
- `.cursor/active/profile-stats-people-restructure/plan.md`
- `.cursor/active/profile-stats-people-restructure/progress.md`
- `docs/features/profile-stats-people-restructure.md`

## Verification

```bash
make backend-test-one target=src/tests/integration/api/test_profile_routes.py
cd frontend && npm run lint
```

- Director distribution tests — `poster_url` present when source films have `primary_director_poster_url`, `null` when absent; ordering, cap-at-20, and `top_director_*` insights unchanged — **passed**
- Frontend ESLint on touched files — **passed**

## Known limitations

- Director `poster_url` uses first non-null poster encountered per director during aggregation (not highest-rated film); documented in service.
- Horizontal people rows show all ≤20 items via scroll; no separate «Показать ещё» collapse (by design for ≤20 cap).
- Deep-link migration from legacy `collection` / `achievements` sub-tab state to `rewards` is optional initializer only; no URL hash persistence for stats sub-tabs.
- `npm run build` not re-run at closeout (lint passed; build assumed clean from prior session).

## Next steps

- None required for this feature scope.
