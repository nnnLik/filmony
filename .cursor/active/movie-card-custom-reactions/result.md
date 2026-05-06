# Result

## Feature
- Slug: `movie-card-custom-reactions`
- Status: implemented

## What Was Implemented
- **БД**: таблицы `reaction_type` (каталог: `label`, `image_url`, `sort_order`, `is_active`) и `user_reaction` (`user_id`, `reaction_type_id`, `target_kind`, `target_id`, unique на пользователя+цель). Миграция: `backend/src/migrations/versions/a1b2c3d4e5f6_reactions.py`.
- **Сервисы** (один публичный `execute` на класс): `ListReactionCatalogService`, `SetOrToggleUserReactionService` (политика self-react: `ALLOW_SELF_REACTION = True` в коде сервиса), `GetReactionSummariesForTargetsService` — батч без N+1 для карточек и комментариев.
- **API**: `GET /api/reactions/catalog`, `POST /api/reactions` с телом `{ target_kind, target_id, reaction_type_id }` (`movie_card` | `movie_card_comment`). Ответ карточки/ленты/комментариев дополнен полем `reactions: { counts, my_reaction_type_id }`.
- **Фронт**: каталог с кешем промисов (`lib/reactionCatalogCache.ts`), `ReactionStrip` (счётчики + нижний sheet-пикер, `@telegram-apps/telegram-ui` `Button`), интеграция в ленту и страницу карточки.
- **Фикстуры**: `fixtures/reaction_type.sql`, порядок в `scripts/load-fixtures.sh`.

## Изменённые / добавленные файлы (основное)
- Backend: см. дерево `backend/src/models/`, `services/reactions/`, `api/reactions/`, правки в `services/cards/list_movie_card_feed.py`, `get_movie_card_details.py`, `list_movie_card_comments.py`, `api/cards/routes.py`, `api/cards/schemas.py`, `api/router.py`.
- Frontend: `api/reactionApi.ts`, `api/profileTypes.ts`, `components/reactions/ReactionStrip.tsx`, `components/feed/FeedCard.tsx`, `pages/MovieCardDetailPage.tsx`, `lib/reactionCatalogCache.ts`.
- Tests: `backend/src/tests/api/test_reactions_routes.py`; `backend/src/tests/api/test_cards_routes.py` (пересобран под новые контракты).

## Совместимость
- **`GET /api/cards/{id}/comments` и replies** теперь требуют сессию (как лента и детали карточки), чтобы вернуть `my_reaction_type_id` без отдельного optional-auth слоя.

## Verification
- Ожидаемая проверка: Docker, `make backend-test` (см. `Makefile`, `.cursor/tech.md`). В этой сессии команда не выполнялась из-за ограничения окружения — запустите локально перед мержем.
- Frontend: `cd frontend && npm run build`.

## Известные ограничения
- Уведомления Telegram о реакциях не реализованы; в сервисе toggle оставлен комментарий-место для будущего события/outbox.
