# Profile Actors Top 20

## Metadata

| Field | Value |
|-------|-------|
| Feature slug | `profile-actors-top20` |
| Status | `in_progress` |
| Stack | fullstack |
| Created | 2026-08-10 |

## Problem

Profile Taste stats expose actor data in ways that are noisy or redundant:

- `actor_distribution` is unbounded and rendered as a donut chart — hard to scan and visually heavy.
- `unique_actors_count` («Актёров») duplicates information already conveyed by the distribution and top-actor insight.
- The metrics strip and donut compete with the more useful «Любимый актёр» insight.

## Goal

Cap backend actor distribution at **top 20** (by rated-film count), drop the **unique actors** metric from the API/insights, and replace the Taste actor donut with a **collapsible ranked list** (10 visible by default, expand to 20). Keep «Любимый актёр» insight unchanged.

## Scope

### In scope

- **Backend:** limit `actor_distribution` to top 20 entries (sorted by `count` desc); remove `unique_actors_count` from profile stats DTO / `insights` payload.
- **Backend:** preserve `top_actor_kinopoisk_id`, `top_actor_name`, `top_actor_count` insight fields.
- **Frontend Taste tab:** remove actor donut chart; show collapsible list of actors (default **10** rows, expand control reveals up to **20**).
- **Frontend metrics strip:** remove «Актёров» metric; keep «Любимый актёр» insight card.
- **Types & tests:** update `profileTypes`, API schemas, and pytest/integration coverage for the new contract.

### Out of scope

- Changes to actor detail page (`/actors/:id`) or rated-cards actor filter behavior beyond consuming the capped distribution list.
- Cast ingestion (`EnsureFilmCastService`, `film_actor` tables) — sibling `actor-cast-profile-stats` / `film-cast-store-all`.
- Personal digest / monthly recap actor fields (unless they reuse the same stats DTO and break without update — fix only if tests fail).

## Acceptance criteria

- [ ] `GET` profile card stats returns `actor_distribution` with **at most 20** items, ordered by `count` descending.
- [ ] Response / `insights` **does not** include `unique_actors_count`.
- [ ] `top_actor_kinopoisk_id`, `top_actor_name`, `top_actor_count` still populated when cast data exists.
- [ ] Taste section: **no** actor donut; collapsible actor list shows **10** by default with control to expand to **20**.
- [ ] Profile metrics strip: **no** «Актёров» item; «Любимый актёр» insight still shown when `top_actor_*` present.
- [ ] Frontend types aligned with backend contract (`unique_actors_count` removed).
- [ ] Backend pytest updated (unit and/or integration per test layout rules); Docker-first verification (`make backend-test` or scoped `make backend-test-one`).
- [ ] Frontend `npm run lint && npm run build` pass on touched files.
- [ ] Closeout docs: `docs/features/profile-actors-top20.md`.

## References

| Path | Purpose |
|------|---------|
| `backend/src/services/profile/get_user_card_stats.py` | Actor distribution + insights assembly |
| `frontend/src/components/profile/ProfileStatsPanel.tsx` | Taste donuts, metrics strip, insights |
| `frontend/src/api/profileTypes.ts` | Client types for stats payload |
| `.cursor/features/actor-cast-profile-stats/feature.md` | Original actor stats feature |
