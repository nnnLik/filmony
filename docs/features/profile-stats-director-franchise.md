# Profile stats: directors and franchises

## Overview

Profile statistics (`GET /api/users/{id}/stats`) now aggregates rated cards by primary director and franchise (series). The Overview sub-tab shows favorite director/series insight cards; the Taste sub-tab adds donut charts with drill-down to rated cards.

## API

Extended fields on `GET /api/users/{id}/stats`:

| Field | Shape | Description |
|-------|-------|-------------|
| `director_distribution` | `{ kinopoisk_id, name, count }[]` | Sorted by count desc |
| `franchise_distribution` | `{ franchise_key, label, count }[]` | Label via `resolve_franchise_label` |
| `insights.top_director_*` | id, name, count | Top director by film count |
| `insights.top_franchise_*` | key, label, count | Top franchise by film count |
| `insights.unique_directors_count` | int | Distinct directors in rated cards |

Cards included: all non-planned (`is_planned=False`), same as other stats aggregates.

## Frontend

- **Overview:** insight cards «Любимый режиссёр», «Любимая серия»; metric strip adds «Режиссёров» when > 0
- **Taste:** «По режиссёрам» and «По сериям» donut charts; click → rated cards filter; link to `/directors`

## Ops

Requires `primary_director_*` and `franchise_key` on `Film` (backfill: `manage_backfill_film_gamification_metadata.py`).

## Tests

- `backend/src/tests/api/test_profile_routes.py::test_user_stats_director_and_franchise_distribution`
- Frontend: `npm run lint && npm run build`
