# actor-cast-profile-stats

## Scope

Top-10 Kinopoisk `ACTOR` cast for rated films only; profile stats + actor detail page (user-scoped).

## Acceptance criteria

- [x] `person` + `film_actor` tables with migration
- [x] `EnsureFilmCastService` on rated create and planned→rated upgrade; not on planned-only
- [x] Backfill command for historical rated films
- [x] Profile stats: `actor_distribution`, `top_actor_*`, `unique_actors_count`
- [x] `GET /api/actors/{kinopoisk_id}` and `/films` (user-scoped)
- [x] Cards filter `actor_kinopoisk_id`
- [x] Frontend: ProfileStatsPanel actors + `ActorDetailPage`
- [x] pytest coverage for new behavior

## Spec

`docs/superpowers/specs/2026-08-08-actor-cast-profile-stats-design.md`
