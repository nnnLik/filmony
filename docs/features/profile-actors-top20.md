# Profile actors: top-20 list

Refines [actor cast profile stats](./actor-cast-profile-stats.md) Taste presentation: caps backend actor distribution at **20**, drops the redundant **unique actors** metric, and replaces the actor donut with a **collapsible ranked list**.

## Summary

| Before | After |
|--------|-------|
| Unbounded `actor_distribution` | At most **20** entries (count desc) |
| `unique_actors_count` in insights + «Актёров» metric strip | Field removed |
| «По актёрам» donut chart (top-8 legend) | Collapsible list: **10** visible, expand to **20** |
| «Любимый актёр» insight | Unchanged |

## Backend

### `GetUserCardStatsService`

- Actor distribution query adds `.limit(20)` after ordering by `count` desc, `Person.name`, `Person.kinopoisk_id`
- `ProfileInsights` no longer includes `unique_actors_count`
- `top_actor_*` fields still populated from the leading actor row

### API contract

- `GET /api/users/{user_id}/stats` — `insights` omits `unique_actors_count`; `actor_distribution` length ≤ 20

## Frontend

### Profile Taste tab (`ProfileStatsPanel`)

- **`ActorDistributionList`** — avatar, name, film count per row; links to `/actors/:kinopoisk_id?userId=…`
- Default **10** rows; «Показать ещё N» button reveals up to **20**
- Metrics strip: no «Актёров» tile; «Любимый актёр» insight card retained

### Types

- `ProfileInsightsSnapshot` — `unique_actors_count` removed

## Key files

- `backend/src/services/profile/get_user_card_stats.py`
- `backend/src/api/profile/schemas.py`
- `backend/src/tests/integration/api/test_profile_routes.py`
- `frontend/src/api/profileTypes.ts`
- `frontend/src/components/profile/ProfileStatsPanel.tsx`

## Verification

```bash
make backend-test-one target=src/tests/integration/api/test_profile_routes.py
cd frontend && npm run lint && npm run build
```

38 profile route integration tests; frontend lint + build clean.
