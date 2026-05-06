# Movie Card Edit/Delete

## Summary
- Добавлена возможность владельцу карточки фильма редактировать оценку и теги.
- Добавлена возможность владельцу удалять карточку через меню действий на detail-экране.
- Backend и frontend синхронизированы owner-only политикой (`403` для чужих карточек).

## Backend
- Новые API:
  - `PATCH /api/cards/{card_id}`
  - `DELETE /api/cards/{card_id}`
- Добавлены сервисы:
  - `UpdateMovieCardService`
  - `DeleteMovieCardService`
- В detail ответ карточки добавлено поле `user_id` для owner-проверки в UI.

## Frontend
- Добавлены API-методы:
  - `updateMovieCard(cardId, payload)`
  - `deleteMovieCard(cardId)`
- На странице карточки `MovieCardDetailPage`:
  - owner-only кнопка `...`;
  - пункты `Редактировать` и `Удалить`;
  - confirm перед удалением и переход в профиль после успеха.
- Добавлена страница `EditMovieCardPage` (`/cards/:cardId/edit`) с предзаполнением:
  - `rating`
  - `company`
  - `mood_before`
  - `mood_after`
  - `custom_tags`
- После edit/delete очищается `myProfileBundleCache`.

## Testing
- Добавлены backend API тесты для:
  - PATCH happy path, validation, `401`, `403`, `404`.
  - DELETE happy path, `401`, `403`, `404`, проверка недоступности карточки после удаления.

## Verification Notes
- В текущей сессии терминальные команды не выполнялись (ограничение среды), поэтому обязательный тестовый прогон должен быть выполнен вручную:
  - `make backend-test-one target=src/tests/api/test_cards_routes.py`
  - `cd frontend && npm run lint`
