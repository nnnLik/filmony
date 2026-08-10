# profile-actors-top20 — result

Status: **complete**

## Implemented

- Backend caps `actor_distribution` at **top 20** actors (sorted by rated-film count desc, tie-break by name and kinopoisk_id)
- Removed `unique_actors_count` from `ProfileInsights` dataclass, API schema, and serialized response
- Preserved `top_actor_kinopoisk_id`, `top_actor_name`, `top_actor_count` insight fields (leader derived from same query before limit)
- Frontend Taste tab: replaced actor donut chart with collapsible ranked list (`ActorDistributionList`) — **10** rows by default, «Показать ещё» expands to **20**
- Frontend metrics strip: removed «Актёров»; «Любимый актёр» insight link unchanged
- Client types aligned: `unique_actors_count` removed from `ProfileInsightsSnapshot`

## Changed files

### Backend
- `backend/src/services/profile/get_user_card_stats.py`
- `backend/src/api/profile/schemas.py`

### Tests
- `backend/src/tests/integration/api/test_profile_routes.py`

### Frontend
- `frontend/src/api/profileTypes.ts`
- `frontend/src/components/profile/ProfileStatsPanel.tsx`

## Verification

```bash
make backend-test-one target=src/tests/integration/api/test_profile_routes.py
cd frontend && npm run lint && npm run build
```

- **38 passed** — `test_profile_routes.py` (Docker)
- Frontend lint and production build — clean

## Known limitations

- Actor list links navigate to `/actors/:id` (actor detail page); donut drill-down to rated-cards filter by actor was removed with the chart
- Distribution cap is server-side only; clients cannot request more than 20 actors
- Director/franchise donuts and distributions unchanged

## Next steps

- None required for this feature scope
