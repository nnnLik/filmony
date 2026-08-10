# Profile stats: directors and franchises

## Overview

Profile statistics (`GET /api/users/{id}/stats`) now aggregates rated cards by primary director and franchise (series). The Overview sub-tab shows favorite director/series insight cards; the Taste sub-tab adds donut charts with drill-down to rated cards.

## API

Extended fields on `GET /api/users/{id}/stats`:

| Field | Shape | Description |
|-------|-------|-------------|
| `director_distribution` | `{ kinopoisk_id, name, count }[]` | Top **20** by count desc — see [profile-directors-top20](./profile-directors-top20.md) |
| `franchise_distribution` | `{ franchise_key, label, count }[]` | Label via `resolve_franchise_label` |
| `insights.top_director_*` | id, name, count | Top director by film count |
| `insights.top_franchise_*` | key, label, count | Top franchise by film count |

Cards included: all non-planned (`is_planned=False`), same as other stats aggregates.

## Frontend

- **Overview:** insight cards «Любимый режиссёр», «Любимая серия» (director insight links to `/directors/:id`)
- **Taste:** «По режиссёрам» collapsible list (top 20, 10 visible) — [profile-directors-top20](./profile-directors-top20.md); «По сериям» donut chart

## Ops

Requires `primary_director_*` and `franchise_key` on `Film` (backfill: `manage_backfill_film_gamification_metadata.py`).

## Tests

- `backend/src/tests/api/test_profile_routes.py::test_user_stats_director_and_franchise_distribution`
- Frontend: `npm run lint && npm run build`
