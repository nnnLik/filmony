# Filmony

[![CI Backend](https://github.com/nnnLik/Filmony/actions/workflows/ci-backend.yml/badge.svg?branch=master)](https://github.com/nnnLik/Filmony/actions/workflows/ci-backend.yml?query=branch%3Amaster)
[![Codecov](https://codecov.io/gh/nnnLik/Filmony/branch/master/graph/badge.svg)](https://codecov.io/gh/nnnLik/Filmony)
[![CI Frontend](https://github.com/nnnLik/Filmony/actions/workflows/ci-frontend.yml/badge.svg?branch=master)](https://github.com/nnnLik/Filmony/actions/workflows/ci-frontend.yml?query=branch%3Amaster)
[![Deploy](https://github.com/nnnLik/Filmony/actions/workflows/deploy.yml/badge.svg)](https://github.com/nnnLik/Filmony/actions/workflows/deploy.yml)
![Python](https://img.shields.io/badge/python-3.13+-3776AB?logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Postgres](https://img.shields.io/badge/Postgres-4169E1?logo=postgresql&logoColor=white)

**Telegram Mini App** для оценки фильмов: шкала 1–10, контекстные теги, рекомендации по «двойникам». Бэкенд — **FastAPI** + **PostgreSQL**; авторизация через Telegram.

Детали стека, сценарии и правила разработки: [`.cursor/tech.md`](.cursor/tech.md), структура репозитория — [`docs/engineering/project-structure-and-style.md`](docs/engineering/project-structure-and-style.md).

## Стек (кратко)

| Слой | Технологии |
|------|------------|
| Frontend | React 19, TypeScript, Vite, Tailwind 4, [@telegram-apps/sdk](https://docs.telegram-mini-apps.com/) |
| Backend | FastAPI, SQLAlchemy 2 async, Alembic, asyncpg, [uv](https://docs.astral.sh/uv/) |
| Данные | PostgreSQL, Redis (в деве — **homelab-infra**, см. `vars/.env.development`) |
| Локальная инфра | `docker-compose.yml` (RustFS, backend, Celery) |

## Структура

```
backend/   frontend/   docs/   vars/
docker-compose.yml   docker-compose.prod.yml   Makefile
```

## Локальная разработка (Docker)

1. Поднять **homelab-infra** (`make dev-up`), сеть **`homelab-infra-network`**. В **`/etc/hosts`**: `filmony-api.localhost`, `filmony.localhost` → `127.0.0.1`.
2. Скопировать/настроить [`vars/.env.development`](vars/.env.development) (Postgres/Redis хосты homelab, `VITE_API_ORIGIN=http://filmony-api.localhost:5080`, `RUSTFS_INTERNAL_BASE_URL=http://rustfs:9000`).
3. `make start` → API **http://127.0.0.1:8888**; через Caddy dev — **http://filmony-api.localhost:5080/** (порт **5080**, не 80). Postgres с хоста: **127.0.0.1:15432**.
4. `make migrate`
5. Фронт отдельно: `cd frontend && npm run dev` (Vite **5176**).

Стикеры в RustFS: `make sync-reactions-rustfs` / `make sync-reactions-rustfs WITH_DB=1` (для БД с хоста порт Postgres подменяется на **15432**, см. `Makefile`).

## Продакшен

Образ backend: **GitHub Actions** → **`ghcr.io/<org>/<repo>/backend:latest`**. На сервере достаточно **`compose.yml`** + `vars/.env.production` (**`GITHUB_REPO`** = `org/repo` в нижнем регистре).

```bash
export GITHUB_REPO=org/repo
make prod-up   # pull + up + alembic upgrade head
```

Деплой из UI: **Actions → Deploy → Run workflow** (секреты `SERVER_*`, для сборки фронта в CI — `VITE_API_ORIGIN`, `VITE_TELEGRAM_BOT_USERNAME`). После деплоя создаётся **GitHub Release** с авто-тегом `deploy-<run>-<attempt>`. Нужны права workflow **Read and write** для `contents` (Settings → Actions → General).

Чеклист: [`.cursor/features/production-readiness/feature.md`](.cursor/features/production-readiness/feature.md).

## Makefile (частое)

| Цель | Назначение |
|------|------------|
| `make start` | dev: build + up |
| `make migrate` / `make prod-migrate` | Alembic upgrade head |
| `make prod-up` | prod: pull GHCR + up + миграции |
| `make backend-test` | pytest в контейнере backend |

