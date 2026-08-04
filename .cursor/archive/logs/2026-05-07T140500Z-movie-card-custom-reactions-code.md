# Log: movie-card-custom-reactions

- **Timestamp:** 2026-05-07T14:05:00Z
- **Feature slug:** `movie-card-custom-reactions`
- **Action type:** code
- **Summary:** Реализованы каталог и пользовательские реакции (toggle/замена), API и сводки в ответах ленты/карточки/комментариев; фронт `ReactionStrip`; миграция и фикстура каталога; тесты reactions + обновлённые cards-тесты; чтение комментариев закрыто сессией как и лента.
- **Files:**
  - `backend/src/migrations/versions/a1b2c3d4e5f6_reactions.py`
  - `backend/src/models/reaction_target_kind.py`, `reaction_type.py`, `user_reaction.py`
  - `backend/src/services/reactions/` (catalog, summaries, toggle)
  - `backend/src/api/reactions/`
  - `backend/src/services/cards/list_movie_card_feed.py`, `get_movie_card_details.py`, `list_movie_card_comments.py`
  - `backend/src/api/cards/routes.py`, `schemas.py`, `backend/src/api/router.py`
  - `fixtures/reaction_type.sql`, `scripts/load-fixtures.sh`
  - `backend/src/tests/api/test_reactions_routes.py`, `backend/src/tests/api/test_cards_routes.py`
  - `frontend/src/api/reactionApi.ts`, `profileTypes.ts`, `lib/reactionCatalogCache.ts`
  - `frontend/src/components/reactions/ReactionStrip.tsx`, `components/feed/FeedCard.tsx`, `pages/MovieCardDetailPage.tsx`
  - `docs/features/movie-card-custom-reactions.md`
- **Verification:** Pending — `make backend-test` inside Docker (`filmony-backend`); локально не запускалось в этой сессии.
