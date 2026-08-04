# Быстрый старт для разработчиков

Практическое руководство: как поднять Filmony локально, прогнать миграции и тесты, задеплоить в прод. О продукте и бейджах CI — в корневом [README](../../README.md).

## Стек (кратко)

| Слой | Технологии |
|------|------------|
| Frontend | React 19, TypeScript, Vite, Tailwind 4, [@telegram-apps/sdk](https://docs.telegram-mini-apps.com/) |
| Backend | FastAPI, SQLAlchemy 2 async, Alembic, asyncpg, [uv](https://docs.astral.sh/uv/) |
| Данные | PostgreSQL, Redis (в деве — **homelab-infra**, см. `vars/.env.development`) |
| Локальная инфра | `docker-compose.yml` (RustFS, backend, Celery) |

**Filmony** — Telegram Mini App для оценки фильмов (шкала 1–10, контекстные теги, рекомендации по «двойникам»). Бэкенд — FastAPI + PostgreSQL; авторизация через Telegram.

## Структура репозитория

```
backend/   frontend/   docs/   vars/
docker-compose.yml   docker-compose.prod.yml   Makefile
```

Подробная карта каталогов и соглашения по коду — [`project-structure-and-style.md`](project-structure-and-style.md).

## Предварительные требования

- **Docker** и **Docker Compose** — для бэкенда, Celery и RustFS.
- **homelab-infra** — отдельный репозиторий с PostgreSQL, Redis и Caddy. Поднять: `make dev-up` (в том репозитории). Сеть Docker: **`homelab-infra-network`**.
- **`/etc/hosts`** — добавить записи `filmony-api.localhost` и `filmony.localhost` → `127.0.0.1`.
- **Node.js** — для фронтенда (`cd frontend && npm install`).
- **uv** (опционально) — pre-commit и скрипты с хоста; в контейнере backend уже есть.

## Локальная разработка (Docker)

Повседневная работа с бэкендом ведётся **из Docker**: исходники монтируются в контейнер `backend` (`docker-compose.yml`, target `dev` в `backend/Dockerfile`).

### Порядок запуска

1. Поднять **homelab-infra** (`make dev-up`), убедиться в сети **`homelab-infra-network`**.
2. Скопировать/настроить [`vars/.env.development`](../../vars/.env.development):
   - хосты Postgres/Redis homelab;
   - `VITE_API_ORIGIN=http://filmony-api.localhost:5080`;
   - `RUSTFS_INTERNAL_BASE_URL=http://rustfs:9000`.
3. Из корня репозитория:

```bash
make start
```

Эквивалент: `docker compose -f docker-compose.yml build && docker compose -f docker-compose.yml up -d`.

4. Применить миграции: `make migrate`.

### Порты и URL

| Сервис | Адрес |
|--------|--------|
| API (прямой) | http://127.0.0.1:8888 |
| API через Caddy (dev) | http://filmony-api.localhost:5080/ (порт **5080**, не 80) |
| Postgres с хоста | 127.0.0.1:**15432** |
| RustFS (скрипты с хоста) | http://127.0.0.1:7900 (см. `sync-reactions-rustfs` в Makefile) |

### Архитектура dev-стека

**homelab-infra**: PostgreSQL, Redis, Caddy. **Этот репозиторий**: RustFS, backend, celery-worker (сеть **`filmony-network`** + подключение к **`homelab-infra-network`**).

```
Telegram Mini App (React) ──► FastAPI (backend)
                                    │
              homelab Postgres ◄────┴────► RustFS
                                    │
                         homelab Redis ◄┘
                                    ▲
                          celery-worker
```

Celery: очередь `default`, **без** Beat — см. [`docs/features/celery-redis-workers.md`](../features/celery-redis-workers.md).

### Стикеры реакций в RustFS

```bash
make sync-reactions-rustfs
make sync-reactions-rustfs WITH_DB=1
```

При `WITH_DB=1` для запуска с хоста порт Postgres подменяется на **15432** (см. `Makefile`).

## Фронтенд

Фронт поднимается **отдельно** от Docker-стека бэкенда:

```bash
cd frontend && npm run dev
```

Vite слушает порт **5176**.

Перед завершением правок в `frontend/`:

```bash
cd frontend && npm run lint && npm run build
```

UI-соглашения (лента, реакции, `IconButton`) — [`docs/frontend/ui-conventions.md`](../frontend/ui-conventions.md).

## Миграции и тесты

### Alembic

```bash
make migrate                    # upgrade head в контейнере backend
make make-migration msg="..."   # autogenerate новой ревизии
```

Ревизии: `backend/src/migrations/versions/`.

### Тесты и качество бэкенда

Все команды ниже выполняются **в контейнере** через Makefile:

```bash
make backend-test
make backend-test-one target=src/tests/api/test_public_routes.py
make backend-test-one target=src/tests/api/test_public_routes.py::test_root
make backend-lint
make backend-format
make backend-fix
```

Без Makefile (compose уже `up`):

```bash
docker compose -f docker-compose.yml exec -w /opt/app backend uv run pytest
docker compose -f docker-compose.yml exec -w /opt/app backend uv run pytest src/tests/api/test_public_routes.py::test_root
```

### Pre-commit (Ruff, только `backend/src/`)

Если `pre-commit` не в PATH: `uv tool install pre-commit`. Один раз: `pre-commit install`. Вручную: `pre-commit run --all-files`. Конфиг: `.pre-commit-config.yaml`, правила Ruff — `backend/pyproject.toml`.

### Фикстуры

```bash
make fixtures-load              # все SQL из fixtures/
make fixtures-load file=path.sql
```

Нужен контейнер **`homelab-postgres`** (homelab-infra `make dev-up`). Порядок — [`scripts/load-fixtures.sh`](../../scripts/load-fixtures.sh).

## Makefile

Частые цели из корневого [`Makefile`](../../Makefile):

| Цель | Назначение |
|------|------------|
| `make start` | dev: `build` + `up` |
| `make build` / `make up` / `make down` | сборка, поднять/остановить compose |
| `make migrate` | Alembic `upgrade head` |
| `make make-migration msg="..."` | autogenerate ревизии |
| `make prod-migrate` | Alembic в прод (см. раздел «Продакшен») |
| `make prod-up` | prod: pull GHCR + up + миграции |
| `make backend-test` | pytest в контейнере backend |
| `make backend-test-one target=…` | один тест/файл (`-n0 --no-cov`) |
| `make backend-lint` / `make backend-format` / `make backend-fix` | Ruff в контейнере |
| `make logs` | логи backend (последние 50 строк, follow) |
| `make celery-worker-logs` | логи celery-worker |
| `make backend-restart` | перезапуск сервиса backend |
| `make fixtures-load` | загрузка SQL-фикстур |
| `make sync-reactions-rustfs` | загрузка стикеров в RustFS (`WITH_DB=1` — синхронизация с БД) |
| `make backfill-film-gamification-metadata` | backfill метаданных геймификации (env: `DRY_RUN`, `FORCE`, `LIMIT`, …) |

## Продакшен

Образ backend собирается в **GitHub Actions** и публикуется как **`ghcr.io/<org>/<repo>/backend:latest`**.

На сервере достаточно **`compose.yml`** (или `docker-compose.prod.yml` из репозитория) + [`vars/.env.production`](../../vars/.env.production). Переменная **`GITHUB_REPO`** = `org/repo` в нижнем регистре.

```bash
export GITHUB_REPO=org/repo
make prod-up   # pull + up + alembic upgrade head
```

Деплой из UI: **Actions → Deploy → Run workflow**. Секреты: `SERVER_*`; для сборки фронта в CI — `VITE_API_ORIGIN`, `VITE_TELEGRAM_BOT_USERNAME`. После деплоя создаётся **GitHub Release** с авто-тегом `deploy-<run>-<attempt>`. Нужны права workflow **Read and write** для `contents` (Settings → Actions → General).

Минимальный прод-контур в [`docker-compose.prod.yml`](../../docker-compose.prod.yml): образ из GHCR, `backend` и `celery-worker`, Postgres/Redis — через homelab-infra.

## Дальнейшее чтение

| Документ | Содержание |
|----------|------------|
| [README](../../README.md) | обзор проекта, CI-бейджи |
| [`.cursor/tech.md`](../../.cursor/tech.md) | архитектура, Celery, целевая модель кеша и рекомендаций |
| [`project-structure-and-style.md`](project-structure-and-style.md) | слои FastAPI, фронт, чеклист перед PR |
| [`docs/frontend/ui-conventions.md`](../frontend/ui-conventions.md) | UI: лента, реакции, иконки |
| [`docs/features/`](../features/) | outcome-доки по доставленным фичам |
