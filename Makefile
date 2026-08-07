DC = docker compose -f docker-compose.yml
DEXEC = docker exec -it -w /opt/app/src
AEXEC = docker exec -it -w /opt/app
AEXEC_NO_TTY = docker exec -w /opt/app
APP = filmony-backend
BACKEND_SERVICE = backend
DLOG = docker logs -f -n 50
RUFF_FMT = ruff format --config /opt/app/pyproject.toml .
RUFF_LINT = ruff check --config /opt/app/pyproject.toml .
RUFF_FIX = ruff check --fix --config /opt/app/pyproject.toml .

.PHONY: start build up down backend-restart make-migration migrate backend-format backend-lint backend-fix backend-test backend-test-unit backend-test-integration backend-test-one fixtures-load sync-reactions-rustfs celery-worker-logs backfill-film-gamification-metadata backfill-film-tmdb-metadata backfill-film-cast diagnose-film-tmdb-metadata seed-letterboxd-top-500 seed-oscars seed-collections seed-achievements sync-film-award-badges

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

backend-test-unit:
	$(AEXEC_NO_TTY) $(APP) uv run pytest src/tests/unit --no-cov -n auto --dist=loadscope

backend-test-integration:
	$(AEXEC_NO_TTY) $(APP) uv run pytest src/tests/integration

backend-test: backend-test-unit backend-test-integration

backend-test-one:
	@test -n "$(target)" || (echo 'usage: make backend-test-one target=src/tests/unit|integration/<dir>/test_<name>::<test_name>' >&2; exit 1)
	$(AEXEC_NO_TTY) $(APP) uv run pytest -n0 --no-cov $(target)

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

backfill-film-gamification-metadata:
	@DRY=$${DRY_RUN:+--dry-run}; \
	FRC=$${FORCE:+--force}; \
	LIM=$${LIMIT:+--limit $$LIMIT}; \
	SKP_STAFF=$${SKIP_STAFF:+--skip-staff}; \
	SKP_SEQ=$${SKIP_SEQUELS:+--skip-sequels}; \
	SLE=$${SLEEP:+--sleep $$SLEEP}; \
	$(AEXEC_NO_TTY) $(APP) python src/manage_backfill_film_gamification_metadata.py \
	  $$DRY $$FRC $$LIM $$SKP_STAFF $$SKP_SEQ $$SLE $(ARGS)

backfill-film-tmdb-metadata:
	@DRY=$${DRY_RUN:+--dry-run}; \
	FRC=$${FORCE:+--force}; \
	FOG=$${FORCE_OVERWRITE:+--force-overwrite-gamification}; \
	LIM=$${LIMIT:+--limit $$LIMIT}; \
	KP_IMDB=$${ALLOW_KP_IMDB_LOOKUP:+--allow-kp-imdb-lookup}; \
	SLE=$${SLEEP:+--sleep $$SLEEP}; \
	$(AEXEC_NO_TTY) $(APP) python src/manage_backfill_film_tmdb_metadata.py \
	  $$DRY $$FRC $$FOG $$LIM $$KP_IMDB $$SLE $(ARGS)

backfill-film-cast:
	@DRY=$${DRY_RUN:+--dry-run}; \
	LIM=$${LIMIT:+--limit $$LIMIT}; \
	SLE=$${SLEEP:+--sleep $$SLEEP}; \
	CON=$${CONCURRENCY:+--concurrency $$CONCURRENCY}; \
	$(AEXEC_NO_TTY) $(APP) python src/manage_backfill_film_cast.py \
	  $$DRY $$LIM $$SLE $$CON $(ARGS)

diagnose-film-tmdb-metadata:
	$(AEXEC_NO_TTY) $(APP) python src/manage_diagnose_film_tmdb_metadata.py $(ARGS)

seed-letterboxd-top-500:
	@DRY=$${DRY_RUN:+--dry-run}; \
	LIM=$${LIMIT:+--limit $$LIMIT}; \
	SLE=$${SLEEP:+--sleep $$SLEEP}; \
	$(AEXEC_NO_TTY) $(APP) python src/manage_seed_letterboxd_top_500.py $$DRY $$LIM $$SLE $(ARGS)

seed-oscars:
	@DRY=$${DRY_RUN:+--dry-run}; \
	LIM=$${LIMIT:+--limit $$LIMIT}; \
	SLE=$${SLEEP:+--sleep $$SLEEP}; \
	YEAR=$${YEAR:+--year $$YEAR}; \
	$(AEXEC_NO_TTY) $(APP) python src/manage_seed_oscars.py $$YEAR $$DRY $$LIM $$SLE $(ARGS)

seed-collections: seed-letterboxd-top-500 seed-oscars

seed-achievements:
	@DRY=$${DRY_RUN:+--dry-run}; \
	$(AEXEC_NO_TTY) $(APP) python src/manage_seed_achievements.py $$DRY $(ARGS)

sync-film-award-badges:
	@DRY=$${DRY_RUN:+--dry-run}; \
	$(AEXEC_NO_TTY) $(APP) python src/manage_sync_film_award_badges.py $$DRY $(ARGS)
