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
#   make backend-test-one target=src/tests/test_routes.py
#   make backend-test-one target=src/tests/test_routes.py::test_root

.PHONY: start build up down backend-restart make-migration migrate backend-format backend-lint backend-fix backend-test backend-test-one

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

# Один файл, класс или тест: make backend-test-one target=src/tests/test_routes.py::test_root
backend-test-one:
	@test -n "$(target)" || (echo 'usage: make backend-test-one target=src/tests/<file>::<test_name>' >&2; exit 1)
	$(DC) exec -w /opt/app $(APP) pytest $(target)

logs:
	$(DC) logs -f -n 50 $(APP)
