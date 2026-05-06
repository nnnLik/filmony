# Progress Log

## Feature
- Slug: `movie-card-custom-reactions`
- Status: done

## Action Entries

### 2026-05-07 14:05 UTC
- Action type: code
- Summary: Модели `ReactionType`, `UserReaction`, миграция Alembic, сервисы каталога/сводок/toggle, роутер `/api/reactions`, агрегаты реакций в ленте, детальной карточке и списках комментариев; фронт `ReactionStrip` + API; тесты `test_reactions_routes.py`; восстановлен/обновлён `test_cards_routes.py` (чтение комментариев теперь требует аутентификацию).
- Files:
  - `backend/src/models/reaction_target_kind.py`, `reaction_type.py`, `user_reaction.py`
  - `backend/src/migrations/versions/a1b2c3d4e5f6_reactions.py`
  - `backend/src/services/reactions/*`
  - `backend/src/api/reactions/`
  - `backend/src/api/cards/*`, сервисы feed/detail/comments
  - `fixtures/reaction_type.sql`, `scripts/load-fixtures.sh`
  - `frontend/src/api/reactionApi.ts`, `profileTypes.ts`, `lib/reactionCatalogCache.ts`, `components/reactions/ReactionStrip.tsx`, `FeedCard.tsx`, `MovieCardDetailPage.tsx`
  - `backend/src/tests/api/test_reactions_routes.py`, `test_cards_routes.py`
