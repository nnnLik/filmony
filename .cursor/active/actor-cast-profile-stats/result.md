# actor-cast-profile-stats — result

Status: **complete**

## Implemented

- `person` + `film_actor` ORM models and Alembic migration from `r3s4t5u6v789`
- `EnsureFilmCastService`: idempotent top-10 Kinopoisk `ACTOR` cast fetch/upsert; KP errors swallowed
- Rated card create and planned→rated upgrade hooks; planned-only cards skip cast
- `manage_backfill_film_cast.py` CLI with dry-run, limit, sleep, batch-size
- Profile stats: `actor_distribution`, `top_actor_*`, `unique_actors_count`; cards filter `actor_kinopoisk_id`
- `GET /api/actors/{kinopoisk_id}` and `/films` (user-scoped via `user_id`)
- Frontend: `actorsApi`, actor insights/donut in `ProfileStatsPanel`, `ActorDetailPage`, rated filter

## Changed files

### Backend
- `backend/src/models/person.py`, `film_actor.py`, `models/__init__.py`
- `backend/src/migrations/versions/s4t5u6v7w890_person_film_actor.py`
- `backend/src/providers/kinopoisk/kinopoisk_staff_dto.py`
- `backend/src/services/cast/parse_top_actors.py`, `ensure_film_cast.py`
- `backend/src/services/cards/create_user_card.py`
- `backend/src/manage_backfill_film_cast.py`
- `backend/src/services/profile/get_user_card_stats.py`, `list_user_cards.py`
- `backend/src/api/profile/schemas.py`, `users_routes.py`
- `backend/src/api/actors/` (routes, schemas)
- `backend/src/services/actors/get_actor_summary.py`, `list_actor_rated_films.py`
- `backend/src/api/router.py`

### Frontend
- `frontend/src/api/actorsApi.ts`, `profileTypes.ts`, `profileApi.ts`
- `frontend/src/components/profile/ProfileStatsPanel.tsx`, `ProfileRatedCardsFilters.tsx`
- `frontend/src/pages/ActorDetailPage.tsx`
- `frontend/src/routes.tsx`
- `frontend/src/lib/ratedCardsListQuery.ts`, `marathonDrillToRatedQuery.ts`

### Tests
- `backend/src/tests/unit/services/cast/test_parse_top_actors.py`
- `backend/src/tests/integration/services/cast/test_ensure_film_cast.py`
- `backend/src/tests/integration/services/cards/test_create_user_card_cast.py`
- `backend/src/tests/integration/scripts/test_manage_backfill_film_cast.py`
- `backend/src/tests/integration/api/test_actors_routes.py`

## Verification

```bash
make backend-test-unit                                    # 166 passed
make backend-test-one target=src/tests/unit/services/cast/
make backend-test-one target=src/tests/integration/services/cast/test_ensure_film_cast.py
make backend-test-one target=src/tests/integration/api/test_actors_routes.py
make backend-test-one target=src/tests/integration/scripts/test_manage_backfill_film_cast.py
cd frontend && npm run lint && npm run build
```

All pass.

## Known limitations

- Cast stored only for top-10 billing-order `ACTOR` entries from Kinopoisk staff
- Existing films need `manage_backfill_film_cast.py` (run after `alembic upgrade head`)
- Actor API returns 404 when person missing or user has zero rated films with that actor

## Next steps

- Run migration + backfill in staging/production
- Manual QA: profile stats donut links, actor detail page, rated cards actor filter
