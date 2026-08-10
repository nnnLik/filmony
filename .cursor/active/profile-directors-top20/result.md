# profile-directors-top20 — result

Status: **complete**

## Implemented

- Backend caps `director_distribution` at **top 20** directors (sorted by rated-film count desc, tie-break by name)
- Removed `unique_directors_count` from `ProfileInsights` dataclass, API schema, and serialized response
- Preserved `top_director_kinopoisk_id`, `top_director_name`, `top_director_count` insight fields (leader from `director_distribution[0]` after full sort, before slice semantics via sorted-then-`[:20]`)
- Frontend Taste tab: replaced director donut with collapsible ranked list (`DirectorDistributionList`) — **10** rows by default, «Показать ещё» expands to **20**
- Frontend metrics strip: removed «Режиссёров»; «Любимый режиссёр» insight retained
- Clickable insight links: «Любимый актёр» and «Любимый режиссёр» navigate to person pages with `userId` query when viewing another user's profile
- Director list rows and «Страница топ-режиссёра →» footer link include `userId` query (parity with actor section)
- Client types aligned: `unique_directors_count` removed from `ProfileInsightsSnapshot`

## Changed files

### Backend
- `backend/src/services/profile/get_user_card_stats.py`
- `backend/src/api/profile/schemas.py`

### Tests
- `backend/src/tests/integration/api/test_profile_routes.py`

### Frontend
- `frontend/src/api/profileTypes.ts`
- `frontend/src/components/profile/ProfileStatsPanel.tsx`
- `frontend/src/components/profile/ProfileStatsCharts.tsx`

## Verification

```bash
make backend-test-one target=src/tests/integration/api/test_profile_routes.py
cd frontend && npm run lint && npm run build
```

- `test_user_stats_director_and_franchise_distribution` — asserts no `unique_directors_count`, `top_director_*` preserved
- `test_user_stats_director_distribution_capped_at_twenty` — max 20 directors, top director count 25 across 25 films
- Frontend lint and production build — clean (closeout)

## Known limitations

- Director list links navigate to `/directors/:id`; donut drill-down to rated-cards filter by director was removed with the chart
- Distribution cap is server-side only; clients cannot request more than 20 directors
- Actor/franchise sections unchanged beyond shared clickable insight links

## Next steps

- None required for this feature scope
