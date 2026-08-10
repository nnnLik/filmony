# Profile directors: top-20 list

Refines [profile stats directors and franchises](./profile-stats-director-franchise.md) Taste presentation: caps backend director distribution at **20**, drops the redundant **unique directors** metric, and replaces the director donut with a **collapsible ranked list**.

## Summary

| Before | After |
|--------|-------|
| Unbounded `director_distribution` | At most **20** entries (count desc) |
| `unique_directors_count` in insights + «Режиссёров» metric strip | Field removed |
| «По режиссёрам» donut chart (top-8 legend) | Collapsible list: **10** visible, expand to **20** |
| «Любимый режиссёр» insight (plain text) | Clickable link to `/directors/:id?userId=…` |
| «Любимый актёр» insight (plain text) | Clickable link to `/actors/:id?userId=…` |

Sibling pattern: [profile-actors-top20](./profile-actors-top20.md).

## Backend

### `GetUserCardStatsService`

- Director distribution built from sorted `director_counts`, sliced to **20** after sort (`[:20]`)
- `ProfileInsights` no longer includes `unique_directors_count`
- `top_director_*` fields derived from `director_distribution[0]` (true #1 before cap)

### API contract

- `GET /api/users/{user_id}/stats` — `insights` omits `unique_directors_count`; `director_distribution` length ≤ 20

## Frontend

### Profile Taste tab (`ProfileStatsPanel`)

- **`DirectorDistributionList`** — avatar, name, film count per row; links to `/directors/:kinopoisk_id?userId=…`
- Default **10** rows; «Показать ещё N» button reveals up to **20**
- Metrics strip: no «Режиссёров» tile; «Любимый режиссёр» insight card with link when id present
- «Страница топ-режиссёра →» footer link under director section (with `userId` when applicable)

### Types

- `ProfileInsightsSnapshot` — `unique_directors_count` removed

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

Integration tests cover director cap, ordering, absence of `unique_directors_count`, and preserved `top_director_*`.
