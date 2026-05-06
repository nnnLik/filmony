---
name: movie-card-create-flow
overview: "Двухэтапная реализация логики создания карточки фильма: сначала создание карточки по существующему film_id, затем интеграция резолва по ссылке Кинопоиска. План учитывает UI-концепт из mock-проекта, стандарты Telegram UI, backend FastAPI и шаг оценки 0.5."
todos:
  - id: phase1-backend-contract
    content: Спроектировать и реализовать backend контракт create card с валидацией rating шагом 0.5 и ошибкой 409 на дубликат
    status: completed
  - id: phase1-frontend-flow
    content: Реализовать frontend страницу создания карточки по film_id с UI в стиле mock-проекта на базе Telegram UI
    status: completed
  - id: phase1-verification
    content: Покрыть backend API/сервисы тестами и проверить frontend lint/build
    status: completed
  - id: phase2-resolve-backend
    content: Добавить backend resolve фильма по ссылке Кинопоиска и idempotent upsert
    status: completed
  - id: phase2-resolve-frontend
    content: Добавить URL-шаг resolve -> preview -> create card в frontend
    status: completed
  - id: phase2-finalize
    content: Обновить документацию фичи, progress/result артефакты и action-log по workflow
    status: completed
isProject: false
---

# План реализации создания карточки

## Зафиксированные решения
- Этапность: сначала `create card` по уже известному `film_id`, затем отдельным этапом `resolve` по ссылке Кинопоиска.
- Повторное создание карточки тем же пользователем на тот же фильм: ошибка `409 Conflict`.
- Оценка: `1..10` с шагом `0.5`, хранение в БД как `FLOAT`.

## Контекст и опорные документы
- Процесс поставки фич: [`/Users/r.makkhmudov/Projects/github/kino/.cursor/rules/feature-delivery-workflow.mdc`](/Users/r.makkhmudov/Projects/github/kino/.cursor/rules/feature-delivery-workflow.mdc).
- Backend-стандарты: [`/Users/r.makkhmudov/Projects/github/kino/.cursor/rules/backend-fastapi-standards.mdc`](/Users/r.makkhmudov/Projects/github/kino/.cursor/rules/backend-fastapi-standards.mdc).
- Frontend-стандарты: [`/Users/r.makkhmudov/Projects/github/kino/.cursor/rules/frontend-react-telegram-ui-standards.mdc`](/Users/r.makkhmudov/Projects/github/kino/.cursor/rules/frontend-react-telegram-ui-standards.mdc).
- Спеки: [`/Users/r.makkhmudov/Projects/github/kino/.cursor/features/004-kinopoisk-movie-by-link.md`](/Users/r.makkhmudov/Projects/github/kino/.cursor/features/004-kinopoisk-movie-by-link.md), [`/Users/r.makkhmudov/Projects/github/kino/.cursor/features/005-movie-rating-with-tags.md`](/Users/r.makkhmudov/Projects/github/kino/.cursor/features/005-movie-rating-with-tags.md).
- UI-память проекта: [`/Users/r.makkhmudov/Projects/github/kino/.cursor/memory/features/telegram-mini-app-ui.md`](/Users/r.makkhmudov/Projects/github/kino/.cursor/memory/features/telegram-mini-app-ui.md).

## Архитектура потока
```mermaid
flowchart TD
  feedEntry[FeedAddEntry] --> createPage[CreateCardPage]
  createPage --> cardApi[POST /api/cards]
  cardApi --> cardService[CreateMovieCardService]
  cardService --> db[(PostgreSQL)]
  cardService --> profileInvalidate[ProfileCardsCacheInvalidate]
  createPage --> profilePage[ProfileCardsList]
  profilePage --> usersCardsApi[GET /api/users/{user_id}/cards]
  usersCardsApi --> listService[ListUserMovieCardsService]
  listService --> db
```

## Этап 1 — Реализация create card (без resolve URL)

### Backend
- Добавить миграции для таблиц карточек:
  - `movie_cards`: `id`, `user_id`, `film_id`, `rating FLOAT`, `company_enum`, `mood_before_enum`, `mood_after_enum`, `created_at`, `updated_at`.
  - `movie_card_tags`: `id`, `movie_card_id`, `tag`, ограничение до 5 тегов на уровне сервиса.
  - Уникальный индекс/констрейнт `(user_id, film_id)` для защиты от дублей.
- Добавить модели и экспорт в [`/Users/r.makkhmudov/Projects/github/kino/backend/src/models/__init__.py`](/Users/r.makkhmudov/Projects/github/kino/backend/src/models/__init__.py).
- Ввести enum-типы домена (company/mood_before/mood_after) в отдельном модуле.
- Реализовать схемы API для карточек:
  - `POST /api/cards` request/response,
  - валидации: `rating` в диапазоне `1..10`, кратность `0.5`, не более 5 custom tags, trim/normalization.
- Реализовать сервисы (по одному действию на сервис):
  - `CreateMovieCardService` (create + проверки + обработка уникальности в `409`),
  - `ListUserMovieCardsService` (заменить stub на реальные данные),
  - `GetUserProfileCountsService` (считать реальное число карточек).
- Подключить новый router карточек в [`/Users/r.makkhmudov/Projects/github/kino/backend/src/api/router.py`](/Users/r.makkhmudov/Projects/github/kino/backend/src/api/router.py).
- Исправить формирование ответа списка карточек в profile API (сейчас возвращается пустой `items`).

### Frontend
- Добавить страницу создания карточки (маршрут в [`/Users/r.makkhmudov/Projects/github/kino/frontend/src/routes.tsx`](/Users/r.makkhmudov/Projects/github/kino/frontend/src/routes.tsx)) в стиле mock, но на Telegram UI + текущих токенах проекта.
- Реализовать entry-point из ленты (`+` / CTA) в [`/Users/r.makkhmudov/Projects/github/kino/frontend/src/pages/FeedPage.tsx`](/Users/r.makkhmudov/Projects/github/kino/frontend/src/pages/FeedPage.tsx).
- На странице создания карточки:
  - film preview для уже известного `film_id`/фильма,
  - контрол оценки с шагом `0.5`,
  - селекторы `company`, `mood before`, `mood after`,
  - ввод до 5 custom tags,
  - submit в `POST /api/cards`.
- Обновить/добавить API-клиент и типы карточек (вместо `unknown[]`) в:
  - [`/Users/r.makkhmudov/Projects/github/kino/frontend/src/api/profileTypes.ts`](/Users/r.makkhmudov/Projects/github/kino/frontend/src/api/profileTypes.ts),
  - [`/Users/r.makkhmudov/Projects/github/kino/frontend/src/api/profileApi.ts`](/Users/r.makkhmudov/Projects/github/kino/frontend/src/api/profileApi.ts) и новый модуль card API.
- Инвалидировать кеш профиля/карточек после успешного создания (учитывая `myProfileBundleCache` из UI-memory).

### Тесты и верификация этапа 1
- Backend (в Docker):
  - тесты API `POST /api/cards` (happy path, `401`, `409`, validation errors),
  - тесты сервиса листинга карточек и счетчика профиля,
  - проверка кратности `0.5` и границ `1..10`.
- Frontend:
  - `npm run lint`, `npm run build`,
  - компонентные/интеграционные тесты для формы карточки (если покрытие настроено в проекте).

## Этап 2 — Интеграция resolve по ссылке Кинопоиска

### Backend
- Реализовать `films` (если еще нет) и endpoint `POST /api/films/resolve` по спецификации 004.
- Парсинг URL Кинопоиска, извлечение external id, upsert фильма, возврат canonical `film_id`.
- Добавить endpoint `GET /api/films/{film_id}` (если нужен фронту для preview/detail).
- Добавить конфиги Kinopoisk API в settings (env-driven).

### Frontend
- На странице создания карточки добавить шаг вставки URL Кинопоиска:
  - ввод URL,
  - loading/error/preview,
  - вызов `POST /api/films/resolve`,
  - переход к форме оценки с предзаполненным `film_id`.
- Визуально повторить концепт из `frontend_example-READONLY` (sticky header, preview, CTA), но через `@telegram-apps/telegram-ui` и существующие стили Filmony.

### Тесты и верификация этапа 2
- Backend: тесты parse/resolve/idempotency/invalid URL.
- Frontend: сценарий `URL -> preview -> create` и обработка ошибок.

## План запуска сабагентов при реализации
- Сабагент A (backend-schema+api): миграции, модели, роуты, сервисы, backend тесты.
- Сабагент B (frontend-create-flow): страницы, UI-компоненты, роутинг, клиент API, cache invalidation.
- Сабагент C (resolve-flow): интеграция Kinopoisk resolve + UI шаг URL (после мержа этапа 1).
- Сабагент D (verification/docs): прогон линтов/тестов, обновление `.cursor/active/*`, `docs/features/*`, action log.

## Риски и меры
- `FLOAT` может давать погрешности сравнения: в валидации и проверках использовать нормализацию (`round(value * 2) / 2`) перед сохранением и сравнением.
- Потенциальная рассинхронизация с profile/list stubs: включить обновление `ListUserMovieCardsService` и profile counts в тот же PR этапа 1.
- Риск UX-мигания из-за кеша профиля: явная инвалидация кеша после create/update карточки.
