---
name: feed-ui-card-design execution
overview: Implement feed card UI with backend-supported feed contracts (comments preview/count), inline commenting from feed, and complete feature workflow artifacts/logging.
todos:
  - id: backend-contract-feed
    content: Add backend feed endpoint + schemas with comments_count/comments_preview and implement service aggregation
    status: completed
  - id: backend-tests-docker
    content: Add/extend backend pytest coverage for feed endpoint and run tests in Docker
    status: completed
  - id: frontend-feed-ui
    content: Implement FeedCard + FeedPage integration with required UI states and CTA navigation
    status: completed
  - id: frontend-inline-comment
    content: Add inline comment composer with optimistic local preview/count update
    status: completed
  - id: artifacts-and-logs
    content: Update progress/result/docs and append action-log entries with verification evidence
    status: completed
isProject: false
---

# Feed UI Card Design — Implementation Plan

## Scope and Outcomes
- Реализовать только `feed-ui-card-design`: карточка ленты (poster/title/rating/tags/comments preview), CTA `Все комментарии`, inline-комментирование с локальным обновлением preview+count.
- Источник данных: **новый backend feed endpoint**.
- Контракт карточки ленты: включает `comments_count` и `comments_preview` в ответе списка.

## Code Areas to Change
- Backend API/contracts/services/tests:
  - [backend/src/api/cards/routes.py](backend/src/api/cards/routes.py)
  - [backend/src/api/cards/schemas.py](backend/src/api/cards/schemas.py)
  - `backend/src/services/cards/*` (новый сервис получения feed карточек с preview комментариев)
  - [backend/src/tests/api/test_cards_routes.py](backend/src/tests/api/test_cards_routes.py)
  - [backend/src/tests/support/db_setup.py](backend/src/tests/support/db_setup.py) (только если нужно для новых test fixtures)
- Frontend API/types/pages/components:
  - [frontend/src/api/cardApi.ts](frontend/src/api/cardApi.ts)
  - [frontend/src/api/profileTypes.ts](frontend/src/api/profileTypes.ts)
  - [frontend/src/pages/FeedPage.tsx](frontend/src/pages/FeedPage.tsx)
  - новый компонент `frontend/src/components/feed/FeedCard.tsx` (+ при необходимости вспомогательные компоненты/скелетоны в этой папке)
  - [frontend/src/routes.tsx](frontend/src/routes.tsx) (только если потребуется привязка/навигация)
- Feature lifecycle artifacts/logging:
  - [.cursor/active/feed-ui-card-design/progress.md](.cursor/active/feed-ui-card-design/progress.md)
  - [.cursor/active/feed-ui-card-design/result.md](.cursor/active/feed-ui-card-design/result.md)
  - [docs/features/feed-ui-card-design.md](docs/features/feed-ui-card-design.md)
  - [.cursor/memory/logs/action-log.md](.cursor/memory/logs/action-log.md) + новый(е) файл(ы) записей в `.cursor/memory/logs/`

## Implementation Steps
1. Backend feed contract design and route wiring
- Добавить response-схемы карточки ленты с полями: movie/meta, rating, system tags (визуальные маркеры), limited custom tags (сырой массив + лимит на frontend), `comments_count`, `comments_preview` (до 2).
- Добавить endpoint получения ленты (в существующем cards API пространстве), не затрагивая алгоритм recommendation вне scope.

2. Backend service for feed items with comments preview
- Реализовать сервис, который возвращает список карточек с предагрегированным `comments_count` и последними 1-2 комментариями на карточку без N+1.
- Сохранить текущие контракты detail/comments API; не ломать существующие страницы.

3. Backend tests in Docker (mandatory)
- Добавить/расширить pytest для:
  - успешного ответа feed endpoint;
  - корректной формы `comments_preview` и `comments_count`;
  - лимитов preview (max 2);
  - auth/validation ошибок при необходимости.
- Запустить backend тесты в Docker (`make backend-test` или `make backend-test-one target=...`) и зафиксировать результаты.

4. Frontend API + types update
- Добавить клиент вызова feed endpoint в `cardApi` (или профильный API-модуль по текущему паттерну).
- Расширить типы карточек ленты в `profileTypes` (или выделить новый feed-тип), включая `comments_count/comments_preview`.

5. Feed card UI component
- Создать `FeedCard` на базе `@telegram-apps/telegram-ui` паттернов проекта:
  - обязательные поля: poster/title/rating;
  - системные теги в визуальном формате (чипы/маркеры);
  - кастомные теги: до 2 + `+N`;
  - preview 1-2 комментариев;
  - CTA `Все комментарии` (navigate в detail).
- Добавить loading skeleton и error/fallback состояния карточки.

6. Inline comment from feed
- В `FeedCard`/`FeedPage` реализовать `Комментировать`: раскрытие composer, отправка через existing comment API.
- После успешной отправки выполнить локальное обновление preview + `comments_count` без полного перефреша ленты и без сброса scroll.
- При ошибке отправки показать понятный UI fallback/retry state.

7. Feed page integration
- Подключить получение данных и рендер списка карточек в `FeedPage` вместо заглушки.
- Обработать loading/empty/error для всей ленты.

8. Frontend verification
- Запустить frontend проверки (минимум lint + релевантные тесты/сборка, исходя из доступных скриптов в проекте).
- Провести ручной smoke сценариев из feature.md: отображение карточки, теги, preview, переход в detail, inline comment, отсутствие horizontal scroll.

9. Required docs and logs
- После каждого meaningful шага обновлять `progress.md`.
- В конце заполнить `result.md`: что сделано, список измененных файлов, команды верификации и итоги, ограничения.
- Обновить `docs/features/feed-ui-card-design.md` по фактически реализованному поведению.
- Добавить action-log entry файлы в `.cursor/memory/logs/` и обновить индекс `action-log.md`.

## Verification Commands (target)
- Backend (Docker-first):
  - `make backend-test-one target=src/tests/api/test_cards_routes.py::<new_or_updated_tests>`
  - `make backend-test` (если по времени допустимо)
- Frontend:
  - `cd frontend && npm run lint`
  - `cd frontend && npm run test` (или релевантный subset, если в проекте принято)

## Risks and Guardrails
- Не трогать unrelated файлы/фичи.
- Не расширять scope до recommendation logic; только UI/contract для feed карточки.
- Сохранить backward compatibility существующих detail/profile сценариев.
