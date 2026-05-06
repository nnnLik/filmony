# Структура репозитория и стиль кода (Filmony)

Документ для разработчиков и агентов: где что лежит, что считать каноничным источником правды, как не плодить мёртвый код и как выровнять стиль бэкенда и фронта **без смены продуктового flow**.

## 1. Карта репозитория

| Путь | Назначение |
|------|------------|
| [`backend/src/`](/backend/src/) | FastAPI-приложение (`main.py`), `api/`, `services/`, `models/`, `migrations/`, `tests/` |
| [`frontend/src/`](/frontend/src/) | React Mini App: `pages/`, `components/`, `api/`, `auth/`, `layout/` |
| [`compose.yml`](/compose.yml) | Локальный стек (Postgres, RustFS, `filmony-backend`) |
| [`fixtures/`](/fixtures/) | SQL-фикстуры; порядок загрузки — [`scripts/load-fixtures.sh`](/scripts/load-fixtures.sh) |
| [`scripts/`](/scripts/) | Утилиты (фикстуры, синхронизация реакций в RustFS) |
| [`.cursor/rules/`](/.cursor/rules/) | Обязательные правила агентов (workflow, FastAPI, React/TGUI) |
| [`.cursor/features/`](/.cursor/features/) | Входящие спеки фич: папки `<slug>/feature.md` + унаследованные нумерованные `.md` |
| [`.cursor/active/<slug>/`](/.cursor/active/) | Живой цикл фичи: `plan.md`, `progress.md`, `result.md` |
| [`.cursor/plans/`](/.cursor/plans/) | Дополнительные планы Cursor (черновики / параллельные сессии) |
| [`.cursor/memory/logs/`](/.cursor/memory/logs/) | Поштучный action log + индекс [`action-log.md`](/.cursor/memory/logs/action-log.md) |
| [`docs/features/`](/docs/features/) | Итоговые outcome-доки по фичам (см. [`README.md`](/docs/features/README.md)) |
| [`docs/frontend/ui-conventions.md`](/docs/frontend/ui-conventions.md) | UI: лента, реакции, `IconButton`, lucide |

Техническое резюме и команды Docker: [`.cursor/tech.md`](/.cursor/tech.md).

## 2. Документация: что канонично

### 2.1. Иерархия

1. **Правила процесса** — `.cursor/rules/` (в т.ч. feature delivery).
2. **Спека фичи** — `.cursor/features/<slug>/feature.md` (шаблон: [`templates/feature-request-template.md`](/.cursor/features/templates/feature-request-template.md)).
3. **Исполнение** — `.cursor/active/<slug>/` (plan / progress / result).
4. **Публичный итог** — `docs/features/<slug>.md` после доставки.

### 2.2. Нумерованные файлы в `.cursor/features/*.md`

Рядом с папками лежат исторические файлы вида `001-…`, `004-…`, `007-…`. После консолидации дорожной карты часть из них помечена как **legacy** и отсылает к актуальным slug’ам и `docs/features/*`. Для новой работы:

- **Канон спеки** — папка `<feature-slug>/feature.md`.
- Нумерованные `.md` **не дублировать** новым контентом; при смене направления — обновлять папку slug и `docs/features`.

### 2.3. `.cursor/plans/*.plan.md`

Файлы в `.cursor/plans/` могут дублировать или дополнять `.cursor/active/<slug>/plan.md`. **Политика:** для «живой» фичи один согласованный план в `.cursor/active/`; содержимое из `.cursor/plans/` при необходимости **переносить или ссылаться** из active, чтобы не расходились два источника.

### 2.4. Сводка: feature slug → артефакты

| Slug (папка в `.cursor/features/`) | `docs/features/*.md` | `.cursor/active/` |
|-----------------------------------|----------------------|------------------|
| `telegram-user-base` | `telegram-user-base.md` | да |
| `profile-and-public-profiles` | `profile-and-public-profiles.md` | да |
| `user-subscriptions` | `user-subscriptions.md` | да |
| `frontend-subscriptions-ui` | `frontend-subscriptions-ui.md` | да |
| `movie-card-create-flow` | `movie-card-create-flow.md` | да |
| `movie-card-comments` | `movie-card-comments.md` | да |
| `movie-card-comments-telegram-like` | `movie-card-comments-telegram-like.md` | да |
| `profile-stats-details` | `profile-stats-details.md` | да |
| `movie-card-edit-delete` | `movie-card-edit-delete.md` | да |
| `feed-ui-card-design` | `feed-ui-card-design.md` | да |
| `feed-recommendation-engine` | `feed-recommendation-engine.md` | да |
| `movie-card-custom-reactions` | `movie-card-custom-reactions.md` | да |
| `telegram-engagement-notifications` | `telegram-engagement-notifications.md` | да |

Итог по Кинопоиску (ссылка из legacy `004-…`): [`docs/features/kinopoisk-movie-by-link.md`](/docs/features/kinopoisk-movie-by-link.md).

## 3. Бэкенд (FastAPI)

### 3.1. Слои и точка входа

- `main.py` → `utils.app_utils` (приложение, CORS, роутер).
- HTTP: `api/**/routes.py` — тонкий слой: валидация, зависимости, вызов **одного** сервиса.
- Бизнес-логика: `services/<domain>/<module>.py` — класс `*Service` с одним публичным методом-входом (`execute` и т.д.), см. `.cursor/rules/backend-fastapi-standards.mdc`.
- Регистрация роутов: [`api/router.py`](/backend/src/api/router.py).

**Де-факто импорты сервисов:** из **конкретного подмодуля**, например `from services.cards.create_movie_card import CreateMovieCardService`, а не через «баррель» пакета. Пакеты `services/cards`, `services/reactions` могут экспортировать `__all__` для удобства точечных импортов (например реакции в карточках) — не смешивайте без причины новый код: либо везде подмодули, либо постепенно выделите тонкий публичный API пакета.

### 3.2. Alembic

- Ревизии: `backend/src/migrations/versions/`.
- Именование: предпочтительно `<revision>_<краткий_slug>.py` для единообразия в код-ревью (исторические короткие имена не переписывать задним числом).

### 3.3. Ruff и качество

- Конфигурация: [`backend/pyproject.toml`](/backend/pyproject.toml). `target-version` согласован с `requires-python`.
- В `ignore` участвует **`F401`** (неиспользуемые импорты) — стандартный `ruff check` их **не подсветит**. Имеет смысл периодически прогонять отдельные инструменты (ниже) или точечно убирать мусор при рефакторинге.

### 3.4. Тесты

Запуск только в Docker, см. корневой [`Makefile`](/Makefile): `make backend-test`, `make backend-test-one target=…`.

## 4. Фронтенд (React + Telegram UI)

### 4.1. Маршруты и точка входа

- Маршруты: [`frontend/src/routes.tsx`](/frontend/src/routes.tsx), оболочка [`AppShell`](/frontend/src/layout/AppShell.tsx).
- Соглашение по импортам: **без суффикса `.tsx`** в путях модулей (единообразие с остальным деревом).

### 4.2. API-слой

- Общий fetch/ошибки: [`api/client.ts`](/frontend/src/api/client.ts).
- Эндпоинты по доменам: `api/cardApi.ts`, `api/profileApi.ts`, `api/reactionApi.ts` и т.д.
- **Мягкая цель:** типы ответов, общие для нескольких модулей, со временем вынести в явный `api/types.ts` или `api/filmTypes.ts` вместо разрастания «чужих» типов в `profileTypes.ts` — без обязательного немедленного рефакторинга.

### 4.3. UI

Обязательно: [`docs/frontend/ui-conventions.md`](/docs/frontend/ui-conventions.md) и `.cursor/rules/frontend-react-telegram-ui-standards.mdc`.

Крупные виджеты разбиты на подпапки рядом с публичным входом (импорты в коде не меняются): например `components/reactions/ReactionStrip.tsx` реэкспортирует из `reactionStrip/`; карточка ленты использует `feedCardUtils.ts` и `FeedCardIcons.tsx`.

- ESLint: `consistent-type-imports`, `no-unused-vars` с префиксом `_` — [`frontend/eslint.config.js`](/frontend/eslint.config.js).

### 4.4. Проверки

```bash
cd frontend && npm run lint && npm run build
```

## 5. Поиск неиспользуемого кода и «висячих» файлов

Автоматика **не даёт 100% гарантии**: динамические импорты, FastAPI-роутинг, Alembic, pytest-плагины и строковые entrypoints дают ложные срабатывания.

### 5.1. TypeScript / React

- **[knip](https://github.com/webpro/knip)** или **ts-prune**: задать entry (`main.tsx`, `vite.config.ts`), исключить `*.d.ts` и конфиги.
- После отчёта — **ручная** проверка: действительно ли символ не используется (динамический `import`, re-export).

### 5.2. Python

- **[vulture](https://github.com/jendelovsky/vulture)** с whitelist для ложных срабатываний (например, имя модуля в Alembic, `pytest_plugins`).
- Дополнительно: просмотр `src/utils`, `src/const` на предмет отсутствия импортов из `api/` и `services/`.

Итог любого автоматического отчёта помечать в PR как «проверено вручную» для спорных символов.

### 5.3. Локальные артефакты

Каталог `tmp/` в корне в [`.gitignore`](/.gitignore) — не коммитить выгрузки HTML/дампы; это не часть сборки.

## 6. Чеклист перед PR

| Слой | Команда |
|------|---------|
| Бэкенд | `make backend-lint`, `make backend-test` (см. [.cursor/tech.md](/.cursor/tech.md)) |
| Фронтенд | `npm run lint`, `npm run build` в `frontend/` |
| Документация фичи | При изменении поведения — актуализировать `docs/features/<slug>.md` и при работе через агентов — action log |

## 7. Устаревшие имена в коде

- `ListReactionCatalogService` — алиас к `ListReactionCatalogGroupedService`; в новом коде предпочитайте **последнее** (см. [`list_reaction_catalog.py`](/backend/src/services/reactions/list_reaction_catalog.py)).

---

*Синхронизация с инфраструктурой: локальный `compose.yml` vs целевой контур (Redis, Celery, Nginx) описана в [`.cursor/tech.md`](/.cursor/tech.md) и [`README.md`](/README.md).*
