# Filmony

Сервис для оценки фильмов с двойной системой оценок (шкала 1–10 и теги контекста) и рекомендациями на основе «двойников» по вкусу. Клиент — **Telegram Mini App**: пользователь открывает приложение внутри Telegram, бэкенд проверяет сессию и хранит данные в **PostgreSQL**.

Подробнее о продукте и дорожной карте см. [`.cursor/tech.md`](.cursor/tech.md) и [`.cursor/user-story.md`](.cursor/user-story.md) (если есть в репозитории). Структура репозитория и стиль кода: [`docs/engineering/project-structure-and-style.md`](docs/engineering/project-structure-and-style.md).

## Стек

| Слой | Технологии |
|------|------------|
| Frontend | React 19, TypeScript, Vite 8, Tailwind CSS 4, [@telegram-apps/sdk](https://docs.telegram-mini-apps.com/) |
| Backend | Python 3.12+, FastAPI, Uvicorn, SQLAlchemy 2 (async), Alembic, asyncpg |
| Данные | PostgreSQL и Redis из **homelab-infra** (дев), см. `vars/.env.development` |
| Сборка / зависимости бэкенда | [uv](https://docs.astral.sh/uv/) (`pyproject.toml`, `uv.lock`) |
| Инфра | `docker-compose.yml` (RustFS, backend, Celery), **homelab-infra** для БД/Redis/Caddy |

## Структура репозитория

```
├── backend/
├── frontend/
├── docs/
├── vars/                  # .env.development, .env.example; прод — .env.production (локально)
├── docker-compose.yml     # dev: rustfs, backend :8888, celery-worker; сети filmony-network + homelab-infra-network
├── docker-compose.prod.yml
└── Makefile
```

## Быстрый старт (Docker)

1. В **homelab-infra**: `make dev-up` (сеть **`homelab-infra-network`**). Caddy: **`filmony-api.localhost`** → API, **`filmony.localhost`** → статика из **`static/filmony/`** (собери `frontend` и скопируй `dist` туда при необходимости). Добавь оба хоста в **`/etc/hosts`** → `127.0.0.1`.

2. В этом репозитории: [`vars/.env.development`](vars/.env.development) — Postgres на `homelab-postgres`, `homelab-redis` (БД и роли создаёшь сам в Postgres), `VITE_API_ORIGIN=http://filmony-api.localhost:5080`, `RUSTFS_INTERNAL_BASE_URL=http://rustfs:9000`.

3. Поднять приложение:

   ```bash
   make start
   ```

   API: **http://127.0.0.1:8888**. Через Caddy в dev шлюз слушает **только порт 5080** (`127.0.0.1:5080`), не 80 — открывай **http://filmony-api.localhost:5080/**. После смены **`caddy/dev/Caddyfile`** перезапусти Caddy в homelab-infra. Postgres с хоста: **127.0.0.1:15432**.

4. Миграции: `make migrate`

5. Фронт: в `frontend/` — `npm run dev` (Vite **5176**); `VITE_API_ORIGIN` берётся из `vars/.env.development`.

6. Стикеры в RustFS:

   ```bash
   make sync-reactions-rustfs
   make sync-reactions-rustfs WITH_DB=1
   ```

   Для `WITH_DB=1` с хоста `homelab-postgres:5432` в URL подменяется на `127.0.0.1:15432` (см. `COMPOSE_PG_PORT` в `Makefile`).

## Продакшен (Compose + GHCR)

Образ бэкенда собирается в **GitHub Actions** и пушится в **`ghcr.io/<org>/<repo>/backend:latest`**. На сервере **не нужен** каталог `backend/` для сборки: только файлы ниже в **`/opt/filmony/`** (или другом каталоге — поправь workflow).

| Файл | Назначение |
|------|------------|
| [`docker-compose.prod.yml`](docker-compose.prod.yml) | `backend` + `celery-worker`, сеть **homelab-infra-network**, Redis только **homelab-redis** (через `CELERY_*` в env) |
| [`Makefile`](Makefile) | `make prod-up`, `make prod-migrate`, `make prod-logs` |
| `vars/.env.production` | Секреты и URL; обязательно **`GITHUB_REPO`** = `org/repo` в **нижнем регистре** (как в GHCR) для подстановки в имя образа |

Первый запуск на сервере после `up`:

```bash
cd /opt/filmony
make prod-migrate
```

Деплой из репозитория: **Actions → Deploy → Run workflow** (те же секреты `SERVER_*`, что и у других сервисов; для фронта в CI: **`VITE_API_ORIGIN`**, **`VITE_TELEGRAM_BOT_USERNAME`**). На сервере должен быть запущен **homelab-infra** (Caddy, Postgres, Redis). В **`vars/.env`** homelab задай **`FILMONY_WEB_HOST`** под HTTPS-статику Mini App (совпадает с origin в **`CORS_ALLOW_ORIGINS`**).

Чеклист: [`.cursor/features/production-readiness/feature.md`](.cursor/features/production-readiness/feature.md).

## Makefile

| Цель | Назначение |
|------|------------|
| `make start` | build + up (dev compose) |
| `make migrate` | Alembic upgrade head (dev) |
| `make prod-up` | pull образов GHCR + up (prod compose) |
| `make prod-migrate` | Alembic upgrade head (prod) |
| `make backend-test` | pytest в контейнере `backend` |
| `make sync-reactions-rustfs WITH_DB=1` | RustFS + БД; хост Postgres homelab — порт **15432** |

## Telegram

- **`/start` в чате** не бьёт в бэкенд без webhook/polling.
- Строка в **`user`** — после **`POST /api/auth/telegram`** из Mini App.
- Подробнее: [`docs/features/telegram-user-base.md`](docs/features/telegram-user-base.md).

## Ссылки

- [Telegram Mini Apps — валидация initData](https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app)
- `.cursor/rules/`, `.cursor/tech.md`
