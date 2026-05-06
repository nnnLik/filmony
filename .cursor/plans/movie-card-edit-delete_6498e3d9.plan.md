---
name: movie-card-edit-delete
overview: "Добавить полноценные owner-only редактирование и удаление movie card: backend API (PATCH/DELETE), frontend UI-меню по образцу из скриншота, форма редактирования rating+всех тегов, и покрытие тестами с обязательной документацией feature workflow."
todos:
  - id: backend-contract
    content: Спроектировать и добавить PATCH/DELETE contracts и owner-only policy (403) в cards API
    status: completed
  - id: backend-tests
    content: Расширить backend tests для PATCH/DELETE и валидаций/permissions
    status: completed
  - id: frontend-api
    content: Добавить update/delete методы в frontend card API слой
    status: completed
  - id: frontend-ui
    content: Добавить action-меню на detail-странице и маршрут/форму редактирования rating+всех тегов
    status: completed
  - id: frontend-delete-flow
    content: Реализовать delete confirm + корректную навигацию/инвалидацию кэша
    status: completed
  - id: artifacts-and-verification
    content: Обновить progress/result/docs/action-log и зафиксировать результаты проверок
    status: completed
isProject: false
---

# План реализации edit/delete карточек

## Цель
Добавить в Telegram Mini App возможность владельцу карточки фильма редактировать `rating`, `company`, `mood_before`, `mood_after`, `custom_tags` и удалять карточку через меню действий на detail-экране.

## Текущее состояние
- Во frontend есть создание и просмотр карточек, но нет action-меню и edit/delete flow.
- В backend есть `POST /api/cards` и `GET /api/cards/{card_id}`, но нет `PATCH/DELETE` для карточки.

## Изменения в backend
1. Добавить схемы обновления карточки в [backend/src/api/cards/schemas.py](backend/src/api/cards/schemas.py):
   - `CardUpdateRequest` (partial update полей: `rating`, `company`, `mood_before`, `mood_after`, `custom_tags`).
   - Переиспользовать текущие валидаторы/ограничения (rating 1..10 шаг 0.5, лимиты тегов).
2. Добавить owner-only endpoints в [backend/src/api/cards/routes.py](backend/src/api/cards/routes.py):
   - `PATCH /api/cards/{card_id}`.
   - `DELETE /api/cards/{card_id}`.
   - Для чужой карточки возвращать `403`.
3. Реализовать сервисы в `backend/src/services/cards/`:
   - `UpdateMovieCardService` (одна публичная точка входа, ownership check, апдейт rating+тегов).
   - `DeleteMovieCardService` (ownership check, удаление карточки).
4. Обновить `cards` тесты в [backend/src/tests/api/test_cards_routes.py](backend/src/tests/api/test_cards_routes.py):
   - PATCH: happy path, `401`, `403`, `404`, `422`.
   - DELETE: happy path (`204`), `401`, `403`, `404`, пост-условие что карточка недоступна.
5. Прогнать backend проверки в Docker по правилам проекта (`make backend-test-one ...`, при необходимости `make backend-test`).

## Изменения во frontend
1. Расширить API-клиент в [frontend/src/api/cardApi.ts](frontend/src/api/cardApi.ts):
   - `updateMovieCard(cardId, payload)` для PATCH.
   - `deleteMovieCard(cardId)` для DELETE.
2. Добавить owner action-меню на detail-экране [frontend/src/pages/MovieCardDetailPage.tsx](frontend/src/pages/MovieCardDetailPage.tsx):
   - Кнопка `...` (как на скриншоте).
   - Пункты: «Редактировать», «Удалить».
   - Показ меню только владельцу карточки.
3. Добавить экран/режим редактирования карточки:
   - либо отдельный `EditCardPage`, либо реюз текущей формы в [frontend/src/pages/CreateCardPage.tsx](frontend/src/pages/CreateCardPage.tsx) в edit-mode.
   - Предзаполнение текущими значениями `rating`, `company`, `mood_before`, `mood_after`, `custom_tags`.
4. Добавить маршрут редактирования в [frontend/src/routes.tsx](frontend/src/routes.tsx) (например, `/cards/:cardId/edit`).
5. Реализовать удаление с confirm-диалогом:
   - После успеха переход на профиль и инвалидация локального кэша профиля (`myProfileBundleCache`) для консистентности списка карточек.
6. Обработать UX-состояния loading/error/success в существующем стиле Telegram UI.

## Документация и feature-артефакты (обязательно по workflow)
1. Обновлять [/.cursor/active/movie-card-comments-telegram-like/progress.md](.cursor/active/movie-card-comments-telegram-like/progress.md) после каждого значимого шага.
2. Создать/обновить `result.md` в `.cursor/active/<feature-slug>/` с проверками и ограничениями.
3. Опубликовать итог в `docs/features/<feature-slug>.md`.
4. Добавить записи в лог действий через индекс [/.cursor/memory/logs/action-log.md](.cursor/memory/logs/action-log.md) и соответствующий фрагмент.

## Проверка готовности
- Backend: тесты cards API (включая новые PATCH/DELETE) проходят в Docker.
- Frontend: ручная проверка сценария владельца (open menu → edit/save, open menu → delete/confirm), сценарий чужой карточки (меню отсутствует / ошибка не проявляется в UI), и отсутствие регрессий detail-экрана.
- Артефакты workflow заполнены: `plan.md`, `progress.md`, `result.md`, `docs/features/...`, action-log записи.
