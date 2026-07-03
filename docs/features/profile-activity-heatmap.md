# Profile Activity Heatmap

## Overview

The profile **Statistics** tab includes a GitHub-style heatmap of viewing activity: each cell is one calendar day; color intensity reflects how many films/games were **completed** that day.

## Placement

- Tab: **Статистика** (not the cards list).
- Position: top of `ProfileStatsPanel`, above the metric strip and charts.
- Works on own profile and public profiles.

## Data rules

| Source | Included in heatmap? |
|--------|----------------------|
| Rated / completed card (`is_planned=false`) | Yes |
| «Позже» / planned snippet (`is_planned=true`) | No |
| Watchlist entry without rated card | No |

Completion timestamp: `user_card.completed_at` (backfilled from `created_at` for existing rows). Set when a card is created as rated or when a planned card is upgraded to rated.

## API

### `GET /api/users/{user_id}/stats`

New fields:

- `activity_distribution`: `{ date, count }[]` (daily buckets, last 90 days / ~3 months UTC)
- `activity_start`, `activity_end`: window bounds (ISO dates)

Query:

- `activity_category_id` (optional): filter activity buckets by shelf only; other stats unchanged.

### `GET /api/users/{user_id}/cards`

Query:

- `completed_on` (optional, `YYYY-MM-DD`): cards completed on that day (for heatmap drill-down).

## UI behavior

- **All shelves** default; chip filter per user category.
- Horizontal scroll on narrow screens; 11px cells (12px on `sm+`).
- Tap a non-empty day → switch to **Карточки → Оценённые** with URL filters `completedOn` and `categoryId` (if a shelf is selected).

## Frontend modules

- `ProfileActivityHeatmap` — grid + shelf chips + legend
- `activityHeatmapGrid.ts` — grid layout and level mapping
- `ratedCardsListQuery.completedOn` — URL-synced drill-down filter
