# Progress Log

## Feature
- Slug: `movie-card-edit-delete`
- Status: in_progress

## Action Entries
### 2026-05-06 20:42 UTC
- Action type: code
- Summary: Добавлены backend контракты и сервисы owner-only update/delete карточки (`PATCH`/`DELETE` с `403` для чужих карточек).
- Files:
  - `backend/src/api/cards/schemas.py`
  - `backend/src/api/cards/routes.py`
  - `backend/src/services/cards/update_movie_card.py`
  - `backend/src/services/cards/delete_movie_card.py`
- Verification:
  - Статический контроль через IDE diagnostics и ревью изменений.

### 2026-05-06 20:48 UTC
- Action type: test
- Summary: Расширены API тесты cards для новых PATCH/DELETE сценариев (auth, permission, validation, post-delete checks).
- Files:
  - `backend/src/tests/api/test_cards_routes.py`
- Verification:
  - Добавлены тестовые сценарии; запуск `make backend-test-one target=src/tests/api/test_cards_routes.py` ожидает ручного прогона (терминальные команды недоступны в сессии).

### 2026-05-06 20:54 UTC
- Action type: code
- Summary: Реализованы frontend edit/delete flows: API-клиенты, detail action menu `...`, отдельная страница редактирования, confirm удаления и cache invalidation.
- Files:
  - `frontend/src/api/cardApi.ts`
  - `frontend/src/api/profileTypes.ts`
  - `frontend/src/pages/MovieCardDetailPage.tsx`
  - `frontend/src/pages/EditMovieCardPage.tsx`
  - `frontend/src/routes.tsx`
- Verification:
  - `ReadLints` для измененных frontend файлов: без ошибок после фикса.
