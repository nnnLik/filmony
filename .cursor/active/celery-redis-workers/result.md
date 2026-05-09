# Результат: celery-redis-workers

## Что сделано

- Redis + Celery worker в Compose; в настройках только **`CELERY_BROKER_URL`** и опционально **`CELERY_RESULT_BACKEND`**.
- `celery_app.py` без дублирования дефолтов Celery (очередь, prefetch, acks — из библиотеки).
- Удалены тестовая задача `tasks/ping`, пакет `tasks/`, тест `test_celery_app.py`.

## Ключевые файлы

- `docker-compose.yml`, `vars/.env.development`, `vars/.env.example`
- `backend/src/conf/settings.py`, `backend/src/celery_app.py`
- `backend/src/tests/conftest.py`
- `docs/features/celery-redis-workers.md`, `README.md`, `.cursor/tech.md`, `Makefile`

## Верификация

- `make backend-test` (в Docker), `make start`, при необходимости `make celery-worker-logs`.
