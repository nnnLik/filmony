# Filmony

Сервис для оценки фильмов с двойной системой оценок (шкала 1–10 и теги контекста) и рекомендациями на основе «двойников» по вкусу. Клиент — **Telegram Mini App**: пользователь открывает приложение внутри Telegram, бэкенд проверяет сессию и хранит данные в **PostgreSQL**.

Подробнее о продукте и дорожной карте см. [`.cursor/tech.md`](.cursor/tech.md) и [`.cursor/user-story.md`](.cursor/user-story.md) (если есть в репозитории).

## Стек

| Слой | Технологии |
|------|------------|
| Frontend | React 19, TypeScript, Vite 8, Tailwind CSS 4, [@telegram-apps/sdk](https://docs.telegram-mini-apps.com/) |
| Backend | Python 3.12+, FastAPI, Uvicorn, SQLAlchemy 2 (async), Alembic, asyncpg |
| Данные | PostgreSQL 16 |
| Сборка / зависимости бэкенда | [uv](https://docs.astral.sh/uv/) (`pyproject.toml`, `uv.lock`) |
| Инфра | Docker Compose (`compose.yml`), Makefile |

В целевой архитектуре также задуманы Redis, Celery, Nginx и бот на webhook — см. `.cursor/tech.md`.

## Структура репозитория

```
├── backend/           # FastAPI-приложение, Alembic, Dockerfile
│   ├── src/           # код приложения (PYTHONPATH указывает сюда в контейнере)
│   ├── alembic.ini
│   └── pyproject.toml
├── frontend/          # Mini App (Vite + React)
├── vars/              # env: версионируемый `.env.development` + `.env.example`
├── compose.yml
└── Makefile
```

## Быстрый старт (Docker)

Разработка бэкенда и тестов рассчитана на **запущенный Compose** (тот же образ, что и в CI/проде).

1. Откройте [`vars/.env.development`](vars/.env.development): там уже выставлены URL для Postgres/RustFS/Vite в связке с `compose.yml`. **Замените плейсхолдеры** `TG_APP_TOKEN` и `KINOPOISK_API_KEY` (и при желании `AUTH_JWT_SECRET`, `TELEGRAM_BOT_USERNAME`) на свои значения. Дополнительный шаблон без значений по умолчанию: [`vars/.env.example`](vars/.env.example).

2. Поднять сервисы:

   ```bash
   make start
   ```

   Бэкенд слушает порт **6749** → `http://127.0.0.1:6749` (см. `compose.yml`). PostgreSQL в compose доступен сервису `filmony-backend` по имени `filmony-postgres`.

3. Миграции БД:

   ```bash
   make migrate
   ```

4. Логи бэкенда:

   ```bash
   make logs
   ```

5. **Стикеры реакций в RustFS** (локальные каталоги в `emoji/`):

   ```bash
   make sync-reactions-rustfs
   # опционально upsert в Postgres (с хоста — порт 55432, см. vars/.env.example):
   DATABASE_URL=postgresql://filmony:filmony@127.0.0.1:55432/filmony make sync-reactions-rustfs ARGS=--sync-db
   ```

   Должны быть запущены compose и RustFS (`http://127.0.0.1:7900`, ключи как в `compose.yml`). Картинки в UI идут через **постоянный** путь `/api/reactions/asset/...`: бэкенд качает объект из RustFS с **подписью S3** при заданных в `vars/.env.development` переменных **`RUSTFS_ACCESS_KEY`** / **`RUSTFS_SECRET_KEY`**. Временные presigned-URL из консоли (порт 7901) для этого не нужны. Подробнее: `docs/features/movie-card-custom-reactions.md`.

## Makefile (бэкенд внутри контейнера)

| Цель | Назначение |
|------|------------|
| `make start` | `docker compose build` + `up -d` |
| `make migrate` | `alembic upgrade head` |
| `make make-migration msg="..."` | автогенерация ревизии Alembic |
| `make backend-test` | весь pytest |
| `make backend-test-one target=src/tests/...` | один тест / файл |
| `make backend-lint` / `backend-format` / `backend-fix` | Ruff |
| `make sync-reactions-rustfs` | залить каталоги `emoji/` в локальный RustFS (нужен `uv` на хосте) |
| `DATABASE_URL=… make sync-reactions-rustfs ARGS=--sync-db` | то же + upsert `reaction_type` (строка подключения должна быть доступна с хоста) |

Тесты используют тот же Postgres, что и приложение; для изоляции данных в pytest выставляется отдельная схема (см. `DATABASE_TEST_SCHEMA` и `src/tests/conftest.py`).

## Фронтенд (локально)

Из каталога `frontend/`:

```bash
npm install
npm run dev
```

Vite по умолчанию проксирует `/api` на бэкенд (настройка `VITE_API_ORIGIN` в `vars/` — см. `frontend/vite.config.ts`).

## Telegram: бот, /start и создание пользователя

- **Сообщение `/start` в чате с ботом** не вызывает ваш бэкенд, пока вы не подняли **обработчик обновлений Bot API** (webhook или polling) в коде — в Filmony этого пока нет.
- **Строка в таблице `user`** создаётся только после **`POST /api/auth/telegram`** из открытого **Mini App** (подписанный `initData`, тот же токен, что у бота — `TG_APP_TOKEN`).
- Что настроить: у бота кнопка/меню **Open Web App** на URL фронта (HTTPS в проде); фронт должен реально ходить на API (`/api/auth/telegram` виден в сети при открытии приложения).

Подробнее: [`docs/features/telegram-user-base.md`](docs/features/telegram-user-base.md).

## Полезные ссылки

- [Telegram Mini Apps — валидация initData](https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app)
- Внутренние правила и сценарии: `.cursor/rules/`, `.cursor/tech.md`
