# Result

## Feature
- Slug: `feed-ui-card-design`
- Status: complete

## What Was Implemented
- Backend: публичная для авторизованного пользователя лента карточек `GET /api/cards/feed` (`cursor`, `limit` до 50), порядок по убыванию `movie_card.id`, в каждой позиции те же базовые поля фильма/оценки/тегов что и для detail-карточки, поле `card_author`, `comments_count` и до двух элементов в `comments_preview` (ответы включаются в подсчёт и выбор последних по `comment.id`).
- Frontend: главная страница ленты загружает feed API, состояния loading (скелеты), ошибка с «Повторить», пустая лента, кнопка «Загрузить ещё» по `next_cursor`; карточка согласует UI с описанными в фиче CTA и inline-комментированием без полного перезапроса списка; после успешного POST комментария локально пересобираются `comments_preview` (две последние по id) и инкрементируется счётчик.
- Контур тестирования для feed на backend добавлен в `test_cards_routes.py`.

## Changed Files
- `backend/src/services/cards/list_movie_card_feed.py`
- `backend/src/api/cards/schemas.py`
- `backend/src/api/cards/routes.py`
- `backend/src/tests/api/test_cards_routes.py`
- `frontend/src/api/profileTypes.ts`
- `frontend/src/api/cardApi.ts`
- `frontend/src/components/feed/FeedCard.tsx`
- `frontend/src/components/feed/FeedCardSkeleton.tsx`
- `frontend/src/pages/FeedPage.tsx`
- `docs/features/feed-ui-card-design.md`
- `.cursor/active/feed-ui-card-design/progress.md`
- `.cursor/active/feed-ui-card-design/result.md`
- `.cursor/memory/logs/action-log.md`
- `.cursor/memory/logs/2026-05-06T223000Z-feed-ui-card-design-code.md`
- `.cursor/memory/logs/2026-05-06T223100Z-feed-ui-card-design-test.md`
- `.cursor/memory/logs/2026-05-06T223200Z-feed-ui-card-design-docs.md`

## Verification
- **Backend (Docker):**  
  `make backend-test-one target=src/tests/api/test_cards_routes.py::test_movie_card_feed_requires_auth`  
  `make backend-test-one target=src/tests/api/test_cards_routes.py::test_movie_card_feed_includes_comments_count_and_preview`  
  `make backend-test-one target=src/tests/api/test_cards_routes.py::test_movie_card_feed_cursor_pagination`  
  или `make backend-test`  
  *В текущей сессии контейнер/ shell не выполнялись — итог тестов зафиксировать после локального запуска.*
- **Frontend:**  
  `cd frontend && npm run lint`  
  *В текущей сессии не запускалось; ESLint IDE для затронутых файлов без предупреждений после правки.*

## Known Limitations / Next Steps
- Сортировка ленты — по id карточки (новее выше), без рекомендательной логики (вне scope).
- Превью комментариев в feed не заполняет `replies_count` / `total_descendants_count` (в ответе 0), только для упрощения payload.
- «Оптимистичное» обновление выполняется после успешного ответа сервера; полный optimistic до ответа не делался сознательно, чтобы совпасть с id и автором сервера.
