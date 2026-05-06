# Backend tests (`src/tests`)

- **`support/`** — окружение pytest: фикстуры (`plugins.py`), подготовка БД (`db_setup.py`). Подключается через `pytest_plugins` из корневого `conftest.py`.
- **`api/`** — тесты публичных HTTP-маршрутов (hello, root).
- **`auth/`** — Telegram / сессия; хелперы рядом (`telegram_init_data.py`).

Корневой **`conftest.py`** только выставляет `ENV=test` и регистрирует плагины — без дублирования логики фикстур.
