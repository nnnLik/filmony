# Progress — profile-and-public-profiles

## Status
- **done** для среза «публичные полки»: бэкенд-ручка, фронт, тесты, документация в этой ветке.

## Log
- Спецификация перенесена в `.cursor/features/profile-and-public-profiles/feature.md`.
- Реализованы бэкенд-маршруты профиля, сервисы, тесты `test_profile_routes.py`.
- Миграция `110da8652616` исправлена: добавление колонок к существующей таблице `user`, а не повторный `create_table`.
- Фронтенд: маршруты `/`, `/profile`, `/u/:identifier`, Telegram UI, клиент API с cookie-сессией.
- Опубликовано `docs/features/profile-and-public-profiles.md`.
- **2026-05-25:** добавлен `GET /api/users/{user_id}/card-categories` и поддержка фильтра «Полка» на публичном профиле чужого пользователя при сохранении `GET /api/me/card-categories` для владельца.
- **2026-05-25:** ленивая загрузка списка полок (только после раскрытия панели фильтров / доп. блока в статистике), усиленный клиентский кеш React Query + session placeholder, очистка при выходе.
