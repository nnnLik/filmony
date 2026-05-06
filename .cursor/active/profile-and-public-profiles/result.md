# Result — profile-and-public-profiles

## Feature
- Slug: `profile-and-public-profiles`
- Final status: **done** (ожидается локальный прогон `make backend-test` / `npm run build` у разработчика)

## Implemented
- Расширена модель пользователя: `profile_slug`, `display_name`, `bio`; уникальный индекс по slug; миграция от `ac3f8989b766` с backfill slug для существующих строк.
- При создании пользователя выдаётся уникальный opaque slug (`AllocateDefaultProfileSlugService`); при логине защитно восстанавливается slug, если отсутствует.
- `GET/PATCH /api/me/profile` — полный редактируемый профиль и счётчики-заглушки (карточки, друзья).
- `GET /api/users/{user_id}`, `GET /api/users/by-slug/{slug}` — публичный профиль для авторизованного зрителя; несуществующий пользователь — **404** (без раскрытия деталей).
- `GET /api/users/{user_id}/cards` — пагинация с параметрами `limit` / `cursor`; v1 — пустой `items`, `next_cursor: null`.
- Настройки `ProfileSettings`: лимиты размера страницы карточек.
- Фронт: `AppRoot` + маршрутизация, экран редактирования своего профиля, экран чужого профиля с кнопкой «Загрузить ещё», вход по `Telegram.WebApp.initData` → `POST /api/auth/telegram`.

## Changed Files
- `backend/src/migrations/versions/110da8652616_enchant_user.py` — корректный upgrade/downgrade для колонок профиля.
- `backend/src/models/user.py`, `backend/src/services/auth/upsert_telegram_user.py`, `backend/src/services/profile/*`, `backend/src/api/profile/*`, `backend/src/api/router.py`, `backend/src/conf/settings.py`
- `backend/src/tests/api/test_profile_routes.py`
- `frontend/package.json`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, новые модули под `frontend/src/api`, `frontend/src/pages`, `frontend/src/hooks`, `frontend/src/components/profile`, `frontend/src/lib`
- `vars/.env.example`, `docs/features/profile-and-public-profiles.md`, `.cursor/features/profile-and-public-profiles/feature.md`, `.cursor/active/profile-and-public-profiles/*`

## Verification
- Commands/checks executed: **не выполнялись** (по запросу пользователя без запуска команд).
- Рекомендуется: `make backend-test`, `make backend-lint`, в каталоге `frontend`: `npm install`, `npm run build`, `npm run lint`.

## Automated tests (backend)
- `backend/src/tests/api/test_profile_routes.py` — покрывает 401 без сессии, свой профиль, PATCH (текст, slug, конфликт slug, лишние поля), публичный профиль по id/slug, 404, пустой список карточек.
- Прогон: `make backend-test` или `make backend-test-one target=src/tests/api/test_profile_routes.py` (в Docker, см. `.cursor/tech.md`).

## Known Limitations
- Счётчики и список карточек — заглушки до фич карточек и друзей.
- Redis-кеш для профиля не подключён (опционально по 002).
- Неавторизованный просмотр профиля не поддерживается (только с httpOnly-сессией).

## Next Steps
- Подключить реальные `movie_cards` и счётчики в сервисах.
- При необходимости — публичные профили без сессии или матрица приватности.
