# Filmony

Сервис для оценки фильмов с двойной системой оценок (шкала 1–10 и теги контекста) и рекомендациями на основе «двойников» по вкусу. Клиент — **Telegram Mini App**: пользователь открывает приложение внутри Telegram, бэкенд проверяет сессию и хранит данные в **PostgreSQL**.

Подробнее о продукте и дорожной карте см. [`.cursor/tech.md`](.cursor/tech.md) и [`.cursor/user-story.md`](.cursor/user-story.md) (если есть в репозитории). Структура репозитория и стиль кода: [`docs/engineering/project-structure-and-style.md`](docs/engineering/project-structure-and-style.md).

## Стек

| Слой | Технологии |
|------|------------|
| Frontend | React 19, TypeScript, Vite 8, Tailwind CSS 4, [@telegram-apps/sdk](https://docs.telegram-mini-apps.com/) |
| Backend | Python 3.12+, FastAPI, Uvicorn, SQLAlchemy 2 (async), Alembic, asyncpg |
| Данные | PostgreSQL (версия образа — см. `compose.yml`) |
| Сборка / зависимости бэкенда | [uv](https://docs.astral.sh/uv/) (`pyproject.toml`, `uv.lock`) |
| Инфра | Docker Compose (`compose.yml`), Makefile; локально также **Redis** и **Celery worker** для фоновых задач |

В **локальном** compose уже есть Redis и Celery worker для отложенных задач; в целевой прод-архитектуре также задуманы Nginx и бот на webhook — см. `.cursor/tech.md`.

## Структура репозитория

```
├── backend/           # FastAPI-приложение, Alembic, Dockerfile
│   ├── src/           # код приложения (PYTHONPATH указывает сюда в контейнере)
│   ├── alembic.ini
│   └── pyproject.toml
├── frontend/          # Mini App (Vite + React)
├── docs/              # итоговые доки фич (`docs/features/`) и инженерные гайды
├── vars/              # env: `.env.development`, `.env.example`, шаблон прод — `.env.production.example`
├── compose.yml        # dev: backend на хосте :8888, Postgres, Redis, RustFS, Celery
├── compose.prod.yml   # prod: backend, Redis, Celery (TLS и прокси — снаружи compose)
└── Makefile
```

## Быстрый старт (Docker)

Разработка бэкенда и тестов рассчитана на **запущенный Compose** (тот же образ, что и в CI/проде).

1. Откройте [`vars/.env.development`](vars/.env.development): там уже выставлены URL для Postgres, RustFS, Redis/Celery и Vite в связке с `compose.yml`. **Замените плейсхолдеры** `TG_APP_TOKEN` и `KINOPOISK_API_KEY` (и при желании `AUTH_JWT_SECRET`, `TELEGRAM_BOT_USERNAME`) на свои значения. Дополнительный шаблон без значений по умолчанию: [`vars/.env.example`](vars/.env.example).

2. Поднять сервисы:

   ```bash
   make start
   ```

   API: **`filmony-backend` на порту 8888** → `http://127.0.0.1:8888`. PostgreSQL из контейнеров — `filmony-postgres:5432`; с хоста — **55432**. После `make start` запустите **`npm run dev`** в `frontend/` (Vite **5176**). В `vars/.env.development` задайте `VITE_API_ORIGIN=http://127.0.0.1:8888` — запросы к API с dev-сервера идут на бэкенд напрямую.

3. Миграции БД:

   ```bash
   make migrate
   ```

4. Логи бэкенда:

   ```bash
   make logs
   ```

   Логи воркера Celery (очередь задач):

   ```bash
   make celery-worker-logs
   ```

5. **Стикеры реакций в RustFS** (локальные каталоги в `emoji/`):

   ```bash
   make sync-reactions-rustfs
   # то же + upsert в БД: из env берётся DATABASE_URL; с хоста `filmony-postgres:5432` подменится на `127.0.0.1:55432` автоматически
   make sync-reactions-rustfs WITH_DB=1
   ```

   Должны быть запущены compose и RustFS (`http://127.0.0.1:7900`, ключи как в `compose.yml`). Картинки в UI идут через **постоянный** путь `/api/reactions/asset/...`: бэкенд качает объект из RustFS с **подписью S3** при заданных в `vars/.env.development` переменных **`RUSTFS_ACCESS_KEY`** / **`RUSTFS_SECRET_KEY`**. Временные presigned-URL из консоли (порт 7901) для этого не нужны. Подробнее: `docs/features/movie-card-custom-reactions.md`.

## Эталонный продакшен (Compose)

Файл **[`compose.prod.yml`](compose.prod.yml)**: образ бэкенда **`target: prod`**, Redis, Celery; порт приложения на хосте (например **8100**) — см. `ports` в compose. Фронт собирается отдельно (Cloudflare Workers/Pages и т.д.).

1. Скопируйте [`vars/.env.production.example`](vars/.env.production.example) → `vars/.env.production`, заполните секреты и URL БД/Redis.
2. `docker compose -f compose.prod.yml build && docker compose -f compose.prod.yml up -d`
3. Миграции: `docker compose -f compose.prod.yml exec filmony-backend alembic upgrade head`

Снаружи TLS и маршрутизация — отдельный reverse proxy (например nginx/Caddy на том же сервере) на порт бэкенда.

Чеклист выката: [`.cursor/features/production-readiness/feature.md`](.cursor/features/production-readiness/feature.md).

## Makefile (бэкенд внутри контейнера)

| Цель | Назначение |
|------|------------|
| `make start` | `docker compose build` + `up -d` |
| `make migrate` | `alembic upgrade head` |
| `make make-migration msg="..."` | автогенерация ревизии Alembic |
| `make backend-test` | весь pytest |
| `make backend-test-one target=src/tests/...` | один тест / файл |
| `make backend-lint` / `backend-format` / `backend-fix` | Ruff |
| `make sync-reactions-rustfs` | только RustFS: каталоги `emoji/` → бакет (нужен `uv`, `make start`) |
| `make celery-worker-logs` | хвост логов контейнера `filmony-celery-worker` |
| `make sync-reactions-rustfs WITH_DB=1` | RustFS + upsert `reaction_type`; из `DATABASE_URL` в `vars/.env.development` для запуска **с хоста** автоматически подставляется `127.0.0.1:55432` вместо `filmony-postgres:5432`. Порт другой — `COMPOSE_PG_PORT=...`. Отключить: `SKIP_DATABASE_URL_HOST_REWRITE=1`. |, что и приложение; для изоляции данных в pytest выставляется отдельная схема (см. `DATABASE_TEST_SCHEMA` и `src/tests/conftest.py`).

## Фронтенд (локально)

Из каталога `frontend/`:

```bash
npm install
npm run dev
```

Сначала `make start`. Vite — **5176**; `VITE_API_ORIGIN` в `vars/` = **`http://127.0.0.1:8888`** (бэкенд в compose), см. `frontend/vite.config.ts`.

## Telegram: бот, /start и создание пользователя

- **Сообщение `/start` в чате с ботом** не вызывает ваш бэкенд, пока вы не подняли **обработчик обновлений Bot API** (webhook или polling) в коде — в Filmony этого пока нет.
- **Строка в таблице `user`** создаётся только после **`POST /api/auth/telegram`** из открытого **Mini App** (подписанный `initData`, тот же токен, что у бота — `TG_APP_TOKEN`).
- Что настроить: у бота кнопка/меню **Open Web App** на URL фронта (HTTPS в проде); фронт должен реально ходить на API (`/api/auth/telegram` виден в сети при открытии приложения).

Подробнее: [`docs/features/telegram-user-base.md`](docs/features/telegram-user-base.md).

## Полезные ссылки

- [Telegram Mini Apps — валидация initData](https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app)
- Внутренние правила и сценарии: `.cursor/rules/`, `.cursor/tech.md`
