# Celery + Redis: отложенные задачи (локальный стек)

Справочник для разработчиков и агентов: очередь, воркер, переменные окружения (**kino / Filmony**).

## Назначение

- **Redis** — брокер Celery; при необходимости тот же Redis может быть **result backend** для `AsyncResult`.
- **Celery worker** — выполняет задачи вне HTTP-запроса.
- **Beat не используется** — только постановка задач в очередь.

## Docker Compose

| Сервис | Контейнер | Назначение |
|--------|------------|------------|
| `filmony-redis` | `filmony-redis` | Redis 8 (Alpine), том `filmony-redis-data` |
| `filmony-celery-worker` | `filmony-celery-worker` | `celery -A celery_app worker --loglevel=INFO` |
| `filmony-backend` | `filmony-backend` | FastAPI; `depends_on` включает Redis |

С хоста Redis: **`127.0.0.1:56379`** → `6379` в контейнере; внутри compose хост **`filmony-redis`**.

## Переменные окружения

| Переменная | Обязательность | Смысл |
|------------|----------------|--------|
| `CELERY_BROKER_URL` | Да | Брокер, в compose: `redis://filmony-redis:6379/0` |
| `CELERY_RESULT_BACKEND` | Нет | Если не задан — `task_ignore_result=True` в `celery_app.py` |

Чтение настроек: `CelerySettings` в `backend/src/conf/settings.py` → `backend/src/celery_app.py`.

## Код

| Путь | Роль |
|------|------|
| `backend/src/celery_app.py` | `app = Celery(...)`, брокер из `settings`, `_register_all_tasks` импортирует `tasks.ping`, `tasks.telegram_engagement` |
| `backend/src/tasks/ping.py` | Пример: `tasks.ping` |
| `backend/src/tasks/telegram_engagement.py` | `tasks.telegram_engagement.notify_comment_reply`, `tasks.telegram_engagement.notify_reaction_added` (уведомления в Telegram) |

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

- `compose.yml`, `Makefile`
- `.cursor/tech.md`
- `.cursor/features/celery-redis-workers/feature.md`
