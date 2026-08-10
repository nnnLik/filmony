# Profile stats: people restructure

Simplifies profile stats navigation, deduplicates Taste vs Social content, and presents directors and actors as horizontal portrait cards with visible photos.

Builds on [profile-directors-top20](./profile-directors-top20.md) and [profile-actors-top20](./profile-actors-top20.md).

## Summary

| Area | Before | After |
|------|--------|-------|
| Gamification tabs | Separate **Коллекция** + **Достижения** | Single **«Награды»** tab (when achievements shown) |
| **Социальность** | Repeated company/mood summary rows | Social-only content (mutual subs, taste quiz, similar profiles) |
| **Вкус** | Company/mood donuts | Unchanged — donuts remain here |
| **По режиссёрам / актёрам** | Vertical ranked lists | Horizontal scroll portrait cards |
| Director API | No `poster_url` on distribution | `director_distribution[].poster_url` (nullable) |

## Backend

### `GetUserCardStatsService`

- `DirectorDistributionItem` extended with `poster_url: str | None`
- While iterating rated cards, tracks per-director poster from `Film.primary_director_poster_url`; keeps first non-null value per director
- Actor aggregation and top-20 cap unchanged

### API contract

- `GET /api/users/{user_id}/stats` — `director_distribution[].poster_url` nullable string aligned with actor distribution shape

## Frontend

### Sub-tab «Награды» (`ProfileStatsPanel`)

- When `showAchievements`: `StatsSubTab` uses `rewards` instead of `collection` + `achievements`
- Renders `ProfilePassportPanel` then `AchievementsPanel` with section headers
- When achievements hidden: collection-only tab set unchanged

### Taste / Social dedupe

- **Вкус:** company and mood donut charts with existing drill behavior
- **Социальность:** removed `watchSummaryRows` / `moodSummaryRows` duplicates

### Horizontal people cards

- **`PersonDistributionStrip`** — shared horizontal scroll row for directors and actors
- Portrait from `poster_url` via `resolveApiMediaUrl`; initials fallback when missing
- Card tap → person page with optional `userId` query param
- Footer links «Страница топ-режиссёра/актёра →» when insights present

### Types

- `DirectorDistributionItem` — added `poster_url?: string | null` (parity with actors)

## Key files

- `backend/src/services/profile/get_user_card_stats.py`
- `backend/src/api/profile/schemas.py`
- `backend/src/tests/integration/api/test_profile_routes.py`
- `frontend/src/api/profileTypes.ts`
- `frontend/src/components/profile/ProfileStatsPanel.tsx`

## Verification

```bash
make backend-test-one target=src/tests/integration/api/test_profile_routes.py
cd frontend && npm run lint
```

Integration tests cover director `poster_url` population (present and absent), distribution ordering, cap at 20, and preserved `top_director_*` insights.
