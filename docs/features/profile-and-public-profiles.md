# Feature: профили и публичные страницы (`profile-and-public-profiles`)

Краткая продуктовая выжимка. Бэклог: [`.cursor/features/002-profile-and-public-profiles.md`](../../.cursor/features/002-profile-and-public-profiles.md), формализация: [`.cursor/features/profile-and-public-profiles/feature.md`](../../.cursor/features/profile-and-public-profiles/feature.md).

## Назначение

Пользователь редактирует **свой** видимый профиль (отображаемое имя, био, короткий **slug** для ссылок). Любой **авторизованный** участник открывает **чужой** профиль по внутреннему UUID или по slug и видит список **карточек фильмов** с пагинацией (`GET /api/users/{user_id}/cards`). Если карточек нет — возвращается пустая страница с тем же контрактом.

Счётчики **подписчиков / подписок** и **числа фильмов** в профиле — реальные поля API (см. [`user-subscriptions.md`](./user-subscriptions.md), [`frontend-subscriptions-ui.md`](./frontend-subscriptions-ui.md)). Модель «друзья» из ранних спек не используется.

## Модель приватности (v1)

- Запросы к чужому профилю и списку карточек требуют **валидной сессии** (JWT в httpOnly cookie после `POST /api/auth/telegram`).
- Если пользователь не найден — ответ **404** (`user not found`), без уточнения причины.

## API

| Метод | Путь | Описание |
|--------|------|----------|
| GET | `/api/me/profile` | Полный профиль текущего пользователя (включая `telegram_user_id` для контекста редактирования). |
| PATCH | `/api/me/profile` | Частичное обновление: `display_name`, `bio`, `profile_slug` (JSON; неизвестные поля — 422). |
| GET | `/api/users/{user_id}` | Публичный профиль по UUID (без `telegram_user_id`). |
| GET | `/api/users/by-slug/{slug}` | Публичный профиль по slug. |
| GET | `/api/users/{user_id}/cards` | Карточки пользователя; query: `limit` (по умолчанию из env), `cursor` (опционально); фильтры (теги, год, компания, настроение, **`category_id` полки** и др.). |
| GET | `/api/users/{user_id}/card-categories` | Полки пользователя (**только для фильтров в профиле**): те же поля, что `/api/me/card-categories`, без создания полки по умолчанию для владельца; несуществующий пользователь — **404**. |

### Коды ошибок (фрагмент)

- **401** — нет сессии.
- **404** — пользователь не найден (публичные GET).
- **409** — slug уже занят при PATCH.
- **422** — невалидный slug, типы полей или тело с лишними ключами.

### Slug

Формат: 3–32 символа, строчные латинские буквы и цифры, внутренние дефисы (`^[a-z0-9][a-z0-9-]{1,30}$`). При первой регистрации выдаётся opaque slug вида `u` + hex.

## Конфигурация (env)

Дополнительно к базовым переменным (см. `docs/features/telegram-user-base.md`):

- `PROFILE_CARDS_PAGE_SIZE_DEFAULT` (по умолчанию `20`)
- `PROFILE_CARDS_PAGE_SIZE_MAX` (по умолчанию `50`)

Шаблон: `vars/.env.example`.

## Миграции

Ревизия `110da8652616` (`enchant-user`): колонки `profile_slug`, `display_name`, `bio` и уникальный индекс на `profile_slug`. На существующих строках slug заполняется из `id`.

## Фронтенд

- Маршруты: `/` (обзор), `/profile` (мой профиль), `/u/:identifier` (UUID или slug).
- Стили и компоненты: `@telegram-apps/telegram-ui`, обёртка `AppRoot`.
- Сессия: при открытии в TMA отправляется `Telegram.WebApp.initData` на `POST /api/auth/telegram` с `credentials: 'include'`.
- Публичный профиль другого пользователя: фильтр **«Полка»** в блоке «Оценённые карточки» подгружает `GET /api/users/{user_id}/card-categories`; свой профиль (в том числе через `/u/...`) по-прежнему использует `GET /api/me/card-categories`, чтобы сохранить гарантированную дефолтную полку и совместимость с редактированием.

## Тесты

- `backend/src/tests/api/test_profile_routes.py`

Прогон в Docker: `make backend-test` (см. `.cursor/tech.md`).

## Статус

Реализовано на бэкенде и фронтенде по контракту v1: профиль, карточки профиля, подписки и счётчики — рабочие. Дополнительно: вкладка статистики по карточкам ([`profile-stats-details.md`](./profile-stats-details.md)).
