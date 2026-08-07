# Action log fragment

- **Timestamp:** 2026-08-07T232200Z
- **Feature slug:** actor-cast-profile-stats
- **Action type:** closeout
- **Summary:** Full actor cast pipeline: Person/FilmActor models, EnsureFilmCast on rated cards, backfill command, profile actor stats + filter, actors API, ActorDetailPage and stats UI. Integration/unit tests green; frontend lint/build pass.

## Files

- `backend/src/models/person.py`, `backend/src/models/film_actor.py`
- `backend/src/migrations/versions/s4t5u6v7w890_person_film_actor.py`
- `backend/src/services/cast/parse_top_actors.py`, `ensure_film_cast.py`
- `backend/src/services/cards/create_user_card.py`
- `backend/src/manage_backfill_film_cast.py`
- `backend/src/services/profile/get_user_card_stats.py`, `list_user_cards.py`
- `backend/src/api/actors/`, `backend/src/services/actors/`
- `frontend/src/api/actorsApi.ts`, `frontend/src/pages/ActorDetailPage.tsx`
- `frontend/src/components/profile/ProfileStatsPanel.tsx`, `ProfileRatedCardsFilters.tsx`
- `docs/features/actor-cast-profile-stats.md`

## Verification

- `make backend-test-unit` — 166 passed
- `make backend-test-one target=src/tests/integration/api/test_actors_routes.py` — 3 passed
- `make backend-test-one target=src/tests/integration/scripts/test_manage_backfill_film_cast.py` — 3 passed
- `cd frontend && npm run lint && npm run build` — pass
