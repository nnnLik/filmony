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
├── vars/              # env-файлы для compose (секреты в .gitignore — см. ниже)
├── compose.yml
└── Makefile
```

## Быстрый старт (Docker)

Разработка бэкенда и тестов рассчитана на **запущенный Compose** (тот же образ, что и в CI/проде).

1. Скопируйте шаблон переменных и подставьте свои значения:

   ```bash
   cp vars/.env.example vars/.env.development
   ```

   Заполните как минимум `DATABASE_URL`, токен Telegram и `AUTH_JWT_SECRET`. Файлы вида `vars/.env.*` с секретами не должны попадать в git (см. `.gitignore`).

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

## Makefile (бэкенд внутри контейнера)

| Цель | Назначение |
|------|------------|
| `make start` | `docker compose build` + `up -d` |
| `make migrate` | `alembic upgrade head` |
| `make make-migration msg="..."` | автогенерация ревизии Alembic |
| `make backend-test` | весь pytest |
| `make backend-test-one target=src/tests/...` | один тест / файл |
| `make backend-lint` / `backend-format` / `backend-fix` | Ruff |

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
