DC = docker compose -f docker-compose.yml
DEXEC = docker exec -it -w /opt/app/src
AEXEC = docker exec -it -w /opt/app
APP = filmony-backend
BACKEND_SERVICE = backend
DLOG = docker logs -f -n 50
RUFF_FMT = ruff format --config /opt/app/pyproject.toml .
RUFF_LINT = ruff check --config /opt/app/pyproject.toml .
RUFF_FIX = ruff check --fix --config /opt/app/pyproject.toml .

.PHONY: start build up down backend-restart make-migration migrate backend-format backend-lint backend-fix backend-test backend-test-one fixtures-load sync-reactions-rustfs celery-worker-logs

start: build up

build:
	$(DC) build

up:
	$(DC) up -d

down:
	$(DC) down

backend-restart:
	$(DC) restart $(BACKEND_SERVICE)

make-migration:
	@test -n "$(msg)" || (echo 'usage: make make-migration msg="your message"' >&2; exit 1)
	$(AEXEC) $(APP) alembic revision --autogenerate -m "$(msg)"

migrate:
	$(AEXEC) $(APP) alembic upgrade head

backend-format:
	$(DEXEC) $(APP) $(RUFF_FMT)

backend-lint:
	$(DEXEC) $(APP) $(RUFF_LINT)

backend-fix:
	$(DEXEC) $(APP) $(RUFF_FIX)

backend-test:
	$(DEXEC) $(APP) pytest

backend-test-one:
	@test -n "$(target)" || (echo 'usage: make backend-test-one target=src/tests/<dir>/test_<name>::<test_name>' >&2; exit 1)
	$(DEXEC) $(APP) pytest $(target)

logs:
	$(DLOG) $(APP)

celery-worker-logs:
	$(DLOG) filmony-celery-worker

fixtures-load:
	@if [ -z "$(file)" ]; then bash scripts/load-fixtures.sh; else bash scripts/load-fixtures.sh "$(file)"; fi

ENV_FILE ?= vars/.env.development
WITH_DB ?= 0
COMPOSE_PG_PORT ?= 15432
SKIP_DATABASE_URL_HOST_REWRITE ?= 0
ARGS ?=
sync-reactions-rustfs:
	bash -c 'set -euo pipefail; \
	  if [[ "$(WITH_DB)" == "1" || "$(WITH_DB)" == "true" || "$(WITH_DB)" == "yes" ]]; then \
	    test -f "$(ENV_FILE)" || { echo "sync WITH_DB=1: нет файла $(ENV_FILE)" >&2; exit 1; }; \
	    set -a; . "./$(ENV_FILE)"; set +a; \
	    if [[ "$(SKIP_DATABASE_URL_HOST_REWRITE)" != "1" && "$${DATABASE_URL:-}" == *"@homelab-postgres:5432"* ]]; then \
	      export DATABASE_URL="$${DATABASE_URL//@homelab-postgres:5432/@127.0.0.1:$(COMPOSE_PG_PORT)/}"; \
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
	  uv run --project backend python scripts/upload_reactions_to_rustfs.py $$DB_FLAG $(ARGS)'
