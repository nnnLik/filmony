# Profile stats: directors and franchises

## Scope

Extend `GET /api/users/{id}/stats` with director and franchise (series) aggregates. Show insight cards on the Overview sub-tab and donut charts on the Taste sub-tab with drill-down to rated cards.

## Acceptance criteria

- API returns `director_distribution`, `franchise_distribution`, and extended `insights` (top director/franchise, unique directors count).
- Overview: insight cards for favorite director and franchise; metric strip shows unique directors when > 0.
- Taste: director and franchise donut sections with click → rated cards filter.
- No new stats sub-tab.
- Backend pytest and frontend lint/build pass.

## Out of scope

- Average rating per director/franchise in distribution.
- Rankings tab top-by-avg.
- Franchises index page.
- Marathon cross-links to Collection tab.
