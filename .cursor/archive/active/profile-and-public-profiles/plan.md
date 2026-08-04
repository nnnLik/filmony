# Implementation Plan — profile-and-public-profiles

## Feature
- Slug: `profile-and-public-profiles`
- Source spec: `.cursor/features/profile-and-public-profiles/feature.md` и [002](../features/002-profile-and-public-profiles.md)

## Goal
Полный контур профиля: бэкенд (модель, миграция, сервисы, маршруты, тесты), фронт (маршрутизация, Telegram UI, сессия через initData), документация и логи workflow.

## Assumptions
- Карточки фильмов (005) ещё нет — отдаём пустой список и счётчик 0.
- Публичный просмотр требует валидной сессии (как в спецификации 002 для v1).

## Step-by-Step Plan
1. БД: миграция `profile_slug`, `display_name`, `bio`; выдача slug при регистрации пользователя.
2. Сервисы: обновление профиля, выборка по id/slug, заглушка списка карточек и счётчиков.
3. API: роуты под `/api/me/profile` и `/api/users/...`; подключение в `api/router.py`.
4. Тесты: `backend/src/tests/api/test_profile_routes.py` (auth, валидация, 404, пустые карточки).
5. Фронт: `react-router-dom`, `@telegram-apps/telegram-ui`, страницы и API-клиент с `credentials: 'include'`.
6. Документация: `docs/features/profile-and-public-profiles.md`; артефакты `.cursor/active/...`; запись во фрагмент action-log (индекс `action-log.md`).
7. **Полки в чужом профиле:** `GET /api/users/{user_id}/card-categories` + клиент `getUserPublicCardCategories`; в UI — `ProfileRatedCardsFilters` с источником `/me`, если профиль свой, иначе публичная ручка; `GET /api/me/card-categories` без удаления логики.
8. **Кеш полок на клиенте:** не запрашивать каталог до раскрытия UI фильтров; усилить `staleTime`/session placeholder как у статистики тегов.

## Files Expected To Change
- `backend/src/migrations/versions/110da8652616_enchant_user.py`
- `backend/src/models/user.py`, `backend/src/services/auth/upsert_telegram_user.py`, `backend/src/services/profile/*`
- `backend/src/api/profile/*`, `backend/src/api/router.py`, `backend/src/conf/settings.py`
- `backend/src/tests/api/test_profile_routes.py`
- `frontend/package.json`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, новые `frontend/src/pages/*`, `frontend/src/api/*`, `frontend/src/hooks/*`, `frontend/src/components/profile/*`
- `vars/.env.example`, `docs/features/profile-and-public-profiles.md`

## Verification Plan
- После поднятия compose: `make backend-test`, `make backend-lint` (выполняет разработчик; в этой сессии команды не запускались).
- Ручная проверка: вход в TMA → «Мой профиль» → сохранение; открытие `/u/<slug>`.

## Risks And Mitigations
- Risk: автогенерация Alembic дублирует таблицу `user`.
  - Mitigation: правка ревизии на `ALTER TABLE` + backfill `profile_slug`.
