# Celery + Redis: отложенные задачи (локальный стек)

Справочник для разработчиков и агентов: очередь, воркер, переменные окружения (**kino / Filmony**).

## Назначение

- **Redis** — брокер Celery; при необходимости тот же Redis может быть **result backend** для `AsyncResult`.
- **Celery worker** — выполняет задачи вне HTTP-запроса.
- **Beat не используется** — только постановка задач в очередь.

## Docker Compose

Локально **Redis** поднимается в **homelab-infra** (`homelab-redis`). В этом репозитории сервис **`celery-worker`** в `docker-compose.yml` ходит в него по `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` из `vars/.env.development` (см. `homelab-postgres`, `homelab-redis`).

| Сервис | Назначение |
|--------|------------|
| `celery-worker` | `celery -A celery_app worker --loglevel=INFO` |
| `backend` | FastAPI |

## Переменные окружения

| Переменная | Обязательность | Смысл |
|------------|----------------|--------|
| `CELERY_BROKER_URL` | Да | Например `redis://homelab-redis:6379/2` (дев, homelab, без пароля в сети Docker) |
| `CELERY_RESULT_BACKEND` | Нет | Если не задан — `task_ignore_result=True` в `celery_app.py` |

Чтение настроек: `CelerySettings` в `backend/src/conf/settings.py` → `backend/src/celery_app.py`.

## Код

| Путь | Роль |
|------|------|
| `backend/src/celery_app.py` | `app = Celery(...)`, брокер из `settings`, `_register_all_tasks` импортирует `tasks.ping`, `tasks.telegram_engagement` |
| `backend/src/tasks/ping.py` | Пример: `tasks.ping` |
| `backend/src/tasks/telegram_engagement.py` | Уведомления в Telegram: комментарии карточки/поста, ответы, @упоминания, реакции, шаринг карточки (см. `docs/features/engagement-telegram-notifications.md`) |

Остальные параметры Celery (очередь по умолчанию, prefetch, acks и т.д.) — **дефолты библиотеки**, не дублируются в env.

## Регистрация задач в этом репозитории

Модули в `backend/src/tasks/` экспортируют **`register_tasks(app: Celery)`**; вызов из `celery_app._register_all_tasks` после создания приложения — без циклических импортов с FastAPI.

## Новая задача

1. Файл в `backend/src/tasks/<name>.py` с функцией **`register_tasks(app: Celery) -> None`**, внутри — `@app.task(name='…')`.

2. В `backend/src/celery_app.py` добавить импорт и вызов в `_register_all_tasks`:

   ```python
   from tasks.my_module import register_tasks as register_my_tasks
   register_my_tasks(application)
   ```

3. Постановка из FastAPI:

   ```python
   from celery_app import app as celery_application

   celery_application.send_task('my.task.name', kwargs={...})
   ```

Для задач, вызывающих существующие **async**-сервисы, см. `tasks.telegram_engagement` (`_run_async_isolated` — отдельный поток + `asyncio.run`, чтобы не конфликтовать с event loop FastAPI при `task_always_eager` в тестах).

Из async FastAPI не блокируйте event loop тяжёлым клиентом без `asyncio.to_thread` / отдельного sync-слоя.

### Устаревший пример (не как в репозитории)

   ```python
   from celery_app import app

   @app.task(name='my_feature.do_something')
   def do_something(user_id: int) -> None:
       ...
   ```

Прямой декоратор на импорте `celery_app` из модулей задач может дать циклический импорт; предпочтителен паттерн **`register_tasks`** выше.

## Логи

`make celery-worker-logs` в корне репозитория.

## Pytest

В `backend/src/tests/conftest.py` задан `CELERY_BROKER_URL` по умолчанию, чтобы `Settings` собирался без полного `.env`.

Регистрация задач: `backend/src/tests/test_celery_app.py`. Уведомления Telegram в тестах используют `task_always_eager` в `test_engagement_telegram_notifications.py`, чтобы `send_task` выполнялся синхронно.

## Ссылки

- `docker-compose.yml`, `Makefile`
- `.cursor/tech.md`
- `.cursor/features/celery-redis-workers/feature.md`
