# Profile Directors Top 20

## Metadata

| Field | Value |
|-------|-------|
| Feature slug | `profile-directors-top20` |
| Status | `complete` |
| Stack | fullstack |
| Created | 2026-08-10 |

## Problem

Profile Taste stats expose director data in ways that are noisy or redundant — mirroring the actor stats issues addressed in `profile-actors-top20`:

- `director_distribution` is unbounded and rendered as a donut chart — hard to scan and visually heavy.
- `unique_directors_count` («Режиссёров») duplicates information already conveyed by the distribution and top-director insight.
- The metrics strip and donut compete with the more useful «Любимый режиссёр» insight.
- Favorite actor and director insight cards in the metrics strip are plain text; users expect taps to open the person profile.

## Goal

Cap backend director distribution at **top 20** (by rated-film count), drop the **unique directors** metric from the API/insights, and replace the Taste director donut with a **collapsible ranked list** (10 visible by default, expand to 20). Keep «Любимый режиссёр» insight unchanged. Make **favorite actor** and **favorite director** insight values **clickable** links to `/actors/:id` and `/directors/:id` (with `userId` query when viewing another user's profile).

## Scope

### In scope

- **Backend:** limit `director_distribution` to top 20 entries (sorted by `count` desc); remove `unique_directors_count` from profile stats DTO / `insights` payload.
- **Backend:** preserve `top_director_kinopoisk_id`, `top_director_name`, `top_director_count` insight fields.
- **Frontend Taste tab:** remove director donut chart; show collapsible list of directors (default **10** rows, expand control reveals up to **20**).
- **Frontend metrics strip:** remove «Режиссёров» metric; keep «Любимый режиссёр» insight card.
- **Frontend metrics strip:** make «Любимый актёр» and «Любимый режиссёр» insight values link to person pages when `top_actor_kinopoisk_id` / `top_director_kinopoisk_id` present.
- **Types & tests:** update `profileTypes`, API schemas, and pytest/integration coverage for the new contract.

### Out of scope

- Changes to director detail page (`/directors/:id`) or rated-cards director filter behavior beyond consuming the capped distribution list.
- Franchise donut / distribution (unchanged in this feature).
- Actor distribution list UX (delivered in `profile-actors-top20`).
- Personal digest / monthly recap director fields (unless they reuse the same stats DTO and break without update — fix only if tests fail).

## Acceptance criteria

- [ ] `GET` profile card stats returns `director_distribution` with **at most 20** items, ordered by `count` descending.
- [ ] Response / `insights` **does not** include `unique_directors_count`.
- [ ] `top_director_kinopoisk_id`, `top_director_name`, `top_director_count` still populated when director data exists.
- [ ] Taste section: **no** director donut; collapsible director list shows **10** by default with control to expand to **20**.
- [ ] Profile metrics strip: **no** «Режиссёров» item; «Любимый режиссёр» insight still shown when `top_director_*` present.
- [ ] Metrics strip: «Любимый актёр» and «Любимый режиссёр» values navigate to `/actors/:kinopoisk_id` and `/directors/:kinopoisk_id` when ids available.
- [ ] Frontend types aligned with backend contract (`unique_directors_count` removed).
- [ ] Backend pytest updated (unit and/or integration per test layout rules); Docker-first verification (`make backend-test` or scoped `make backend-test-one`).
- [ ] Frontend `npm run lint && npm run build` pass on touched files.
- [ ] Closeout docs: `docs/features/profile-directors-top20.md`.

## References

| Path | Purpose |
|------|---------|
| `backend/src/services/profile/get_user_card_stats.py` | Director distribution + insights assembly |
| `frontend/src/components/profile/ProfileStatsPanel.tsx` | Taste donuts, metrics strip, insights |
| `frontend/src/api/profileTypes.ts` | Client types for stats payload |
| `.cursor/features/profile-actors-top20/feature.md` | Sibling actor top-20 feature (pattern) |
| `.cursor/features/profile-stats-director-franchise/feature.md` | Original director stats feature |
