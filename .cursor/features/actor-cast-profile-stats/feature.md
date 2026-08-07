# actor-cast-profile-stats

## Scope

Top-10 Kinopoisk `ACTOR` cast for rated films only; profile stats + actor detail page (user-scoped).

## Acceptance criteria

- [ ] `person` + `film_actor` tables with migration
- [ ] `EnsureFilmCastService` on rated create and planned→rated upgrade; not on planned-only
- [ ] Backfill command for historical rated films
- [ ] Profile stats: `actor_distribution`, `top_actor_*`, `unique_actors_count`
- [ ] `GET /api/actors/{kinopoisk_id}` and `/films` (user-scoped)
- [ ] Cards filter `actor_kinopoisk_id`
- [ ] Frontend: ProfileStatsPanel actors + `ActorDetailPage`
- [ ] pytest coverage for new behavior

## Spec

`docs/superpowers/specs/2026-08-08-actor-cast-profile-stats-design.md`
