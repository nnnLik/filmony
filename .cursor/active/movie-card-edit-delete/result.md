# Result

## Feature
- Slug: `movie-card-edit-delete`
- Status: in_progress

## What Was Implemented
- Добавлены backend endpoints:
  - `PATCH /api/cards/{card_id}` для редактирования `rating`, `company`, `mood_before`, `mood_after`, `custom_tags`.
  - `DELETE /api/cards/{card_id}` для удаления карточки.
- Реализованы сервисы:
  - `UpdateMovieCardService` с ownership check и валидацией.
  - `DeleteMovieCardService` с ownership check.
- Политика доступа: для чужой карточки edit/delete возвращают `403`.
- Расширен detail контракт карточки полем `user_id` для owner UX на frontend.
- Во frontend добавлены:
  - API методы `updateMovieCard` и `deleteMovieCard`.
  - Меню действий `...` на detail-экране (owner-only).
  - Отдельная страница редактирования `/cards/:cardId/edit`.
  - Confirm-удаление, очистка `myProfileBundleCache`, переход в профиль после удаления.

## Changed Files
- `backend/src/api/cards/schemas.py`
- `backend/src/api/cards/routes.py`
- `backend/src/services/cards/update_movie_card.py`
- `backend/src/services/cards/delete_movie_card.py`
- `backend/src/tests/api/test_cards_routes.py`
- `frontend/src/api/cardApi.ts`
- `frontend/src/api/profileTypes.ts`
- `frontend/src/pages/MovieCardDetailPage.tsx`
- `frontend/src/pages/EditMovieCardPage.tsx`
- `frontend/src/routes.tsx`

## Verification
- Выполнено:
  - `ReadLints` для измененных frontend/backend файлов: актуальных lint ошибок не осталось.
- Требуется ручной прогон:
  - `make backend-test-one target=src/tests/api/test_cards_routes.py`
  - `cd frontend && npm run lint`
  - ручной UI smoke test для owner edit/delete сценариев.
- Причина частичного статуса:
  - Терминальные команды в текущей сессии отклоняются средой, поэтому автоматический прогон тестов не выполнен.

## Known Limitations
- Для полного `done` статуса нужны фактические результаты тестового прогона команд выше.
