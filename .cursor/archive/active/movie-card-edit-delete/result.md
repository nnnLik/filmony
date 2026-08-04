# Result

## Feature
- Slug: `movie-card-edit-delete`
- Status: done

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
- В этой closeout-правке новые проверки не запускались.
- Историческая запись о реализации и ранее добавленных тестах сохранена в `progress.md` и action-log.

## Known Limitations
- Ограничения этой closeout-правки отсутствуют; оставшиеся замечания относятся к исходной реализации и уже зафиксированы в старых записях.
