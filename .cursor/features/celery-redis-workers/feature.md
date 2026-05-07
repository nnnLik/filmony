# Feature: Celery + Redis (отложенные задачи)

## Цель

Локальный стек: **Redis** как брокер Celery и **воркер** для фоновых задач. Без Celery Beat.

## Acceptance criteria

- [x] В `compose.yml`: Redis, `filmony-celery-worker`, `filmony-backend` зависит от Redis.
- [x] `celery[redis]` в `backend/pyproject.toml` и `uv.lock`.
- [x] `CelerySettings` + `celery_app.py` (только `CELERY_BROKER_URL` / опционально `CELERY_RESULT_BACKEND`).
- [x] Документация: `docs/features/celery-redis-workers.md`.

## Slug

`celery-redis-workers`
