# Feature Result

## Feature
- Slug: `telegram-user-base`
- Final status: **in_progress** (бэкенд + тесты + инфра; фронт по полному чеклисту 001 — не завершён)

## Implemented
- Проверка Telegram Mini App `initData` (HMAC по правилам WebAppData), отказ с 401 при невалидных данных.
- Upsert пользователя в PostgreSQL (модель `User`, таблица по имени из `Base.__tablename__` → `user`).
- Сессия: JWT HS256 в httpOnly cookie (`SESSION_COOKIE_NAME` / по умолчанию `filmony_session`).
- API: `POST /api/auth/telegram`, `GET /api/me`, `POST /api/auth/logout`; зависимость `CurrentUser`.
- Настройки БД и auth в `conf/settings.py`; движок и сессии в `core/database.py`.
- Alembic: `backend/alembic.ini`, `backend/src/migrations/`; миграция `001_users`.
- Docker Compose: Postgres + backend; Makefile-цели для pytest, migrate, lint.
- Pytest: отдельная схема БД при `ENV=test` (см. `conftest.py`), тесты auth.
- Репозиторий: `.gitignore`, `README.md`, `vars/.env.example`; устранено предупреждение Pydantic о поле `schema` (переименовано в `default_schema`, env `DATABASE_SCHEMA` без изменений).

## Changed Files (основные)
- `backend/src/conf/settings.py` — окружение приложения и БД.
- `backend/src/core/database.py` — asyncpg, search_path для тестов.
- `backend/src/api/auth/routes.py`, `schemas.py` — контракты auth.
- `backend/src/api/router.py` — `/api/me`, подключение auth-router.
- `backend/src/deps/auth.py`, `deps/db.py` — текущий пользователь, сессия БД.
- `backend/src/services/auth/*` — verify initData, upsert, JWT.
- `backend/src/models/user.py`, `models/base.py` (наследование как в проекте).
- `backend/src/migrations/env.py`, `versions/001_users.py`
- `backend/src/tests/conftest.py`, `test_telegram_auth.py`, `telegram_auth_helpers.py`
- `compose.yml`, `Makefile`, `backend/Dockerfile`
- `.gitignore`, `README.md`, `vars/.env.example`

## Verification
- Ожидаемая команда: `make start` затем `make migrate` затем `make backend-test`.
- Итог в этой сессии: автоматический прогон pytest в Docker не был приложен к логу как артефакт; при необходимости выполните локально и допишите строку сюда.

## Automated tests (backend)
- `backend/src/tests/test_telegram_auth.py` — невалидный hash, просроченный auth_date, успешный обмен + cookie + `/api/me`, идемпотентность, logout.
- `backend/src/tests/test_routes.py` — существующие smoke-тесты.
- Хелпер: `backend/src/tests/telegram_auth_helpers.py`.

## Known Limitations
- Фронт: в спецификации 001 указаны `api/client.ts`, `useTelegramAuth`, `AuthContext` и доработка `App.tsx` под бэкенд-пользователя — в текущем дереве фронта этого нет или объём меньше спеки; нужна отдельная итерация.
- Секреты: если `vars/.env.development` когда-либо коммитился, нужна ротация токенов и `git rm --cached` для игнорируемых файлов.

## Next Steps
- Завершить фронт по 001 (initData → POST, `credentials: 'include'`, состояния загрузки/ошибки).
- Прогнать `make backend-test`, зафиксировать вывод в этом файле и в action-log.
