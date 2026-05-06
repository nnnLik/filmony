DC = docker compose -f compose.yml
DEXEC = docker exec -it -w /opt/app/src
APP = filmony-backend
DLOG = docker logs -f -n 50
RUFF_FMT = ruff format --config pyproject.toml src/
RUFF_LINT = ruff check --config pyproject.toml src/
RUFF_FIX = ruff check --fix --config pyproject.toml src/

# Docker-first: поднимайте стек (`make start`), затем вызывайте цели ниже — они выполняются внутри контейнера `filmony-backend`.
# Примеры pytest:
#   make backend-test
#   make backend-test-one target=src/tests/api/test_public_routes.py
#   make backend-test-one target=src/tests/api/test_public_routes.py::test_root

.PHONY: start build up down backend-restart make-migration migrate backend-format backend-lint backend-fix backend-test backend-test-one fixtures-load sync-reactions-rustfs

start: build up

build:
	$(DC) build

up:
	$(DC) up -d

down:
	$(DC) down

backend-restart:
	$(DC) restart $(APP)

make-migration:
	@test -n "$(msg)" || (echo 'usage: make make-migration msg="your message"' >&2; exit 1)
	$(DC) exec -w /opt/app $(APP) alembic revision --autogenerate -m "$(msg)"

migrate:
	$(DC) exec -w /opt/app $(APP) alembic upgrade head

backend-format:
	$(DC) exec -w /opt/app $(APP) $(RUFF_FMT)

backend-lint:
	$(DC) exec -w /opt/app $(APP) $(RUFF_LINT)

backend-fix:
	$(DC) exec -w /opt/app $(APP) $(RUFF_FIX)

# Все тесты бэкенда (pytest + pytest-asyncio); требуется запущенный compose.
backend-test:
	$(DC) exec -w /opt/app $(APP) pytest

# Один файл, класс или тест: make backend-test-one target=src/tests/api/test_public_routes.py::test_root
backend-test-one:
	@test -n "$(target)" || (echo 'usage: make backend-test-one target=src/tests/<dir>/test_<name>::<test_name>' >&2; exit 1)
	$(DC) exec -w /opt/app $(APP) pytest $(target)

logs:
	$(DC) logs -f -n 50 $(APP)

# Загрузка SQL-фикстур в Postgres (контейнер filmony-postgres должен быть запущен: make start).
# Все файлы: make fixtures-load
# Один файл из fixtures/: make fixtures-load file=user.sql
fixtures-load:
	@if [ -z "$(file)" ]; then bash scripts/load-fixtures.sh; else bash scripts/load-fixtures.sh "$(file)"; fi

# Залить `emoji/*-emojigg-pack` в RustFS (S3). Нужны: `make start` (RustFS на localhost:7900), на хосте — `uv`.
# Только объекты:     make sync-reactions-rustfs
# RustFS + upsert БД:  make sync-reactions-rustfs WITH_DB=1
#   (source `vars/.env.development`; для хоста `DATABASE_URL` с `filmony-postgres:5432`
#    подменяется на `127.0.0.1:$(COMPOSE_PG_PORT)`, см. ниже COMPOSE_PG_PORT)
# Отключить подмену:     SKIP_DATABASE_URL_HOST_REWRITE=1 make sync-reactions-rustfs WITH_DB=1
# Доп. флаги скрипта:  make sync-reactions-rustfs ARGS='--help'
# Переопределить S3:    RUSTFS_ENDPOINT=... make sync-reactions-rustfs
ENV_FILE ?= vars/.env.development
WITH_DB ?= 0
COMPOSE_PG_PORT ?= 55432
SKIP_DATABASE_URL_HOST_REWRITE ?= 0
ARGS ?=
sync-reactions-rustfs:
	bash -c 'set -euo pipefail; \
	  if [[ "$(WITH_DB)" == "1" || "$(WITH_DB)" == "true" || "$(WITH_DB)" == "yes" ]]; then \
	    test -f "$(ENV_FILE)" || { echo "sync WITH_DB=1: нет файла $(ENV_FILE)" >&2; exit 1; }; \
	    set -a; . "./$(ENV_FILE)"; set +a; \
	    if [[ "$(SKIP_DATABASE_URL_HOST_REWRITE)" != "1" && "$${DATABASE_URL:-}" == *"@filmony-postgres:5432"* ]]; then \
	      export DATABASE_URL="$${DATABASE_URL//@filmony-postgres:5432/@127.0.0.1:$(COMPOSE_PG_PORT)/}"; \
	      echo "sync WITH_DB=1: DATABASE_URL -> 127.0.0.1:$(COMPOSE_PG_PORT) для запуска с хоста" >&2; \
	    fi; \
	    DB_FLAG=--sync-db; \
	  else \
	    DB_FLAG=; \
	  fi; \
	  export RUSTFS_ENDPOINT="$${RUSTFS_ENDPOINT:-http://127.0.0.1:7900}"; \
	  export RUSTFS_ACCESS_KEY="$${RUSTFS_ACCESS_KEY:-rustfsadmin}"; \
	  export RUSTFS_SECRET_KEY="$${RUSTFS_SECRET_KEY:-rustfsadmin}"; \
	  export RUSTFS_BUCKET="$${RUSTFS_BUCKET:-filmony-reactions}"; \
	  uv run --project backend python scripts/sync_reactions_to_rustfs.py $$DB_FLAG $(ARGS)'
