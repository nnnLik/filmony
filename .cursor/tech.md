# Техническая документация (кратко)

## 1. Проект
Сервис для оценки фильмов с двойной системой оценок (оценка 1-10 + теги контекста) и рекомендациями на основе "двойников". Работает через Telegram Mini App.

## 2. Архитектура

### 2.1. Локальная разработка (`compose.yml`)

Текущий репозиторий поднимает для day-to-day работы:

```
Telegram Mini App (React) ──► FastAPI (Uvicorn, filmony-backend)
                                    │
                    PostgreSQL ◄────┴────► RustFS (S3-совместимое хранилище медиа реакций)
```

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

Nginx, Redis, Celery и бот на webhook в **этом** `compose.yml` могут отсутствовать — см. описание в корневом `README.md`.

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
| Кеш | Redis | в целевой архитектуре |
| Очереди | Celery (брокер — Redis) | в целевой архитектуре |
| Reverse proxy | Nginx | в целевой архитектуре |
| Уведомления в реальном времени | SSE | по необходимости |
| Фронтенд | React + @telegram-apps/telegram-ui + **lucide-react** (иконки) + Vite + TypeScript | |
| Интеграция | Telegram Bot API, Kinopoisk API Unofficial | |

Подробнее про ленту, `ReactionStrip`, `IconButton` и центрирование иконок: **[`docs/frontend/ui-conventions.md`](../docs/frontend/ui-conventions.md)**.

Структура репозитория и соглашения по стилю: **[`docs/engineering/project-structure-and-style.md`](../docs/engineering/project-structure-and-style.md)**.

## 5. Основной функционал

**Пользователи:** друзья (заявки, принятие), подписки.

**Карточки фильмов:** создание по ссылке с Кинопоиска (парсинг названия, постера, года). Заполнение: оценка 1-10, теги "компания", "настроение до", "настроение после", до 5 своих тегов.

**Приглашения:** если смотрел не один — отправить друзьям на заполнение (только их оценка и настроение после).

**Комментарии и лайки:** к карточкам и комментариям.

**Лента:** карточки друзей + редкие вкидки от незнакомцев с похожим вкусом.

**Рекомендации:** ручные (кинуть другу) и автоматические через "двойников".

**Профили:** чужие профили с их карточками для ручного поиска совпадений.

## 6. Рекомендательная система (целевая модель)

В целевой реализации: вектор пользователя в Redis; при добавлении оценки — пересчёт близости к другим; смешанный коэффициент (оценки + теги); кеш двойников; уведомления при сильных совпадениях. Текущая реализация в коде — см. `docs/features/feed-recommendation-engine.md` и сервисы ленты.

## 7. Кеширование (Redis, целевая модель)

Лента, оценки друзей на карточке, топ по фильму, двойники — с TTL. В локальном compose Redis может отсутствовать.

## 8. Фоновые задачи (Celery, целевая модель)

Тяжёлые задачи: парсинг, векторы, уведомления, пересборка кешей. В репозитории контур Celery может быть подключён только на проде.

## 9. Деплой

VPS (2-4 ГБ RAM, 20 ГБ SSD) + Docker Compose. Минимум: Postgres + приложение; полный контур — Postgres, Redis, FastAPI, Nginx, Celery, Telegram Bot на webhook.
