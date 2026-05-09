# Техническая документация (кратко)

## 1. Проект
Сервис для оценки фильмов с двойной системой оценок (оценка 1-10 + теги контекста) и рекомендациями на основе "двойников". Работает через Telegram Mini App.

## 2. Архитектура

### 2.1. Локальная разработка (`docker-compose.yml` + homelab-infra)

**homelab-infra** (`make dev-up`): PostgreSQL, Redis, Caddy. Этот репозиторий: **RustFS**, **backend**, **celery-worker** (сеть `homelab` + `app`).

```
Telegram Mini App (React) ──► FastAPI (backend)
                                    │
              homelab Postgres ◄────┴────► RustFS
                                    │
                         homelab Redis ◄┘
                                    ▲
                          celery-worker
```

- **Celery**: очередь `default`, **без** Beat — см. [`docs/features/celery-redis-workers.md`](../docs/features/celery-redis-workers.md).
- Порты и порядок запуска — [`README.md`](../README.md).

### 2.2. Целевая / продуктовая архитектура

В полном контуре (прод, roadmap) задумано также:

```
Telegram Mini App (React) → Nginx → FastAPI (Uvicorn)
                           ↓
              PostgreSQL ←→ Redis ←→ Celery
                                    ↓
                              Telegram Bot
```

Nginx и бот на webhook в корневом compose не обязательны — см. `README.md`. Воркер Celery — в `docker-compose.yml`; Redis в homelab.

## 3. Локальная разработка (Docker)

Повседневная работа с бэкендом ведётся **из Docker**: исходники монтируются в контейнер `backend` (`docker-compose.yml`, `backend/Dockerfile` target `dev`).

**Поднять стек и бэкенд:**

```bash
make start
# эквивалентно: docker compose -f docker-compose.yml build && docker compose -f docker-compose.yml up -d
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
docker compose -f docker-compose.yml exec -w /opt/app backend pytest
docker compose -f docker-compose.yml exec -w /opt/app backend pytest src/tests/api/test_public_routes.py::test_root
```

## 4. Стек

| Компонент | Технология | Примечание |
|-----------|-----------|------------|
| Бэкенд | FastAPI + Uvicorn | в Docker |
| База данных | PostgreSQL | homelab-infra (дев) |
| Объектное хранилище | RustFS (S3 API) | медиа реакций, см. `docs/features/movie-card-custom-reactions.md` |
| Кеш / брокер | **Redis** (homelab-infra, дев) |
| Очереди | **Celery** + Redis (`celery-worker`), без Beat — см. `docs/features/celery-redis-workers.md` |
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

Лента, оценки на карточке, топ по фильму, двойники (когда появятся) — в целевой модели с TTL. **Redis для Celery** — в homelab; отдельного кеша ленты в Redis в текущей реализации может не быть — см. `docs/features/feed-recommendation-engine.md`.

## 8. Фоновые задачи (Celery, целевая модель)

Тяжёлые задачи: парсинг, векторы, уведомления, пересборка кешей. **Celery worker** — сервис `celery-worker` в `docker-compose.yml`; прод — см. `docker-compose.prod.yml` и `docs/features/celery-redis-workers.md`.

## 9. Деплой

VPS (2-4 ГБ RAM, 20 ГБ SSD) + Docker Compose. Минимум: Postgres + приложение; полный контур — Postgres, Redis, FastAPI, Nginx, Celery, Telegram Bot на webhook.
