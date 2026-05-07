# Техническая документация (кратко)

## 1. Проект
Сервис для оценки фильмов с двойной системой оценок (оценка 1-10 + теги контекста) и рекомендациями на основе "двойников". Работает через Telegram Mini App.

## 2. Архитектура

### 2.1. Локальная разработка (`compose.yml`)

Текущий репозиторий поднимает для day-to-day работы:

```
Telegram Mini App (React) ──► FastAPI (Uvicorn, filmony-backend)
                                    │
                    PostgreSQL ◄────┴────► RustFS
                                    │
                              Redis ◄┘
                                    ▲
                          Celery worker (filmony-celery-worker)
```

- **Redis** (`filmony-redis`): брокер сообщений и backend результатов Celery; с хоста порт **56379** → `6379` в контейнере.
- **Celery** (`filmony-celery-worker`): отложенные задачи (очередь `default`), **без** Celery Beat — периодическое расписание не используется.

Подробности для разработчиков и агентов: [`docs/features/celery-redis-workers.md`](../docs/features/celery-redis-workers.md).

Порты и имена сервисов см. в корневом `compose.yml` и `README.md`.

### 2.2. Целевая / продуктовая архитектура

В полном контуре (прод, roadmap) задумано также:

```
Telegram Mini App (React) → Nginx → FastAPI (Uvicorn)
                           ↓
              PostgreSQL ←→ Redis ←→ Celery
                                    ↓
                              Telegram Bot
```

Nginx и бот на webhook в **этом** `compose.yml` по-прежнему могут отсутствовать — см. корневой `README.md`. **Redis и Celery worker** включены в локальный compose для фоновых задач.

## 3. Локальная разработка (Docker)

Повседневная работа с бэкендом ведётся **полностью из Docker**: исходники монтируются в контейнер, зависимости и интерпретатор — только внутри образа (`compose.yml`, сервис `filmony-backend`, `backend/Dockerfile` target `dev`).

**Поднять стек и бэкенд:**

```bash
make start
# эквивалентно: docker compose -f compose.yml build && docker compose -f compose.yml up -d
```

**Типовые команды (всё выполняется в контейнере через Makefile):**

```bash
make backend-lint
make backend-format
make backend-test
make backend-test-one target=src/tests/api/test_public_routes.py
make backend-test-one target=src/tests/api/test_public_routes.py::test_root
```

**Те же действия без Makefile** (из корня репозитория, compose уже `up`):

```bash
docker compose -f compose.yml exec -w /opt/app filmony-backend pytest
docker compose -f compose.yml exec -w /opt/app filmony-backend pytest src/tests/api/test_public_routes.py::test_root
```

## 4. Стек

| Компонент | Технология | Примечание |
|-----------|-----------|------------|
| Бэкенд | FastAPI + Uvicorn | в Docker |
| База данных | PostgreSQL | в локальном compose см. образ в `compose.yml` |
| Объектное хранилище | RustFS (S3 API) | медиа реакций, см. `docs/features/movie-card-custom-reactions.md` |
| Кеш / брокер | **Redis** (локально в compose, сервис `filmony-redis`) |
| Очереди | **Celery** + Redis (`filmony-celery-worker`), без Beat — см. `docs/features/celery-redis-workers.md` |
| Reverse proxy | Nginx | в целевой архитектуре |
| Уведомления в реальном времени | SSE | по необходимости |
| Фронтенд | React + @telegram-apps/telegram-ui + **lucide-react** (иконки) + Vite + TypeScript | |
| Интеграция | Telegram Bot API, Kinopoisk API Unofficial | |

Подробнее про ленту, `ReactionStrip`, `IconButton` и центрирование иконок: **[`docs/frontend/ui-conventions.md`](../docs/frontend/ui-conventions.md)**.

Структура репозитория и соглашения по стилю: **[`docs/engineering/project-structure-and-style.md`](../docs/engineering/project-structure-and-style.md)**.

## 5. Основной функционал

**Пользователи:** асимметричные **подписки** (follow); модель «заявки в друзья» из ранних спек не используется.

**Карточки фильмов:** создание по ссылке с Кинопоиска (парсинг названия, постера, года). Заполнение: оценка 1–10 (шаг 0.5), теги «компания», «настроение до», «настроение после», до 5 своих тегов.

**Приглашения / шаринг:** отправить карточку в Telegram **своим подписчикам** (они же получатели DM); отдельный упрощённый поток «только оценка и настроение после для приглашённого» может быть отдельной фичей.

**Комментарии и реакции:** к карточкам и комментариям; лайки комментариев — см. доки фич.

**Лента:** карточки из подписок и подписчиков, персональный сигнал без ML и слоты discovery — см. `docs/features/feed-recommendation-engine.md`.

**Рекомендации:** ручной шаринг; автоматические «двойники» (008) — в дорожной карте, вне минимальной формулы ленты.

**Профили:** чужие профили с карточками и статистикой для ручного поиска совпадений.

## 6. Рекомендательная система (целевая модель)

В целевой реализации: вектор пользователя в Redis; при добавлении оценки — пересчёт близости к другим; смешанный коэффициент (оценки + теги); кеш двойников; уведомления при сильных совпадениях. Текущая реализация в коде — см. `docs/features/feed-recommendation-engine.md` и сервисы ленты.

## 7. Кеширование (Redis, целевая модель)

Лента, оценки на карточке, топ по фильму, двойники (когда появятся) — в целевой модели с TTL. **Локальный** `compose.yml` уже поднимает **Redis** (`filmony-redis`) для Celery; отдельного кеша ленты в Redis в текущей реализации может не быть — см. `docs/features/feed-recommendation-engine.md`.

## 8. Фоновые задачи (Celery, целевая модель)

Тяжёлые задачи: парсинг, векторы, уведомления, пересборка кешей. **В репозитории** контур **Celery worker** включён в локальный compose (`filmony-celery-worker`), очередь Redis; прод-развёртывание должно поднимать worker там же, где нужна доставка Telegram engagement — см. `docs/features/celery-redis-workers.md`.

## 9. Деплой

VPS (2-4 ГБ RAM, 20 ГБ SSD) + Docker Compose. Минимум: Postgres + приложение; полный контур — Postgres, Redis, FastAPI, Nginx, Celery, Telegram Bot на webhook.
