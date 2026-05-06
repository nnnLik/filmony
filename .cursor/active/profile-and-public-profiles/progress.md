# Progress — profile-and-public-profiles

## Status
- **done** (код и документы в репозитории; запуск тестов — на стороне разработчика)

## Log
- Спецификация перенесена в `.cursor/features/profile-and-public-profiles/feature.md`.
- Реализованы бэкенд-маршруты профиля, сервисы, тесты `test_profile_routes.py`.
- Миграция `110da8652616` исправлена: добавление колонок к существующей таблице `user`, а не повторный `create_table`.
- Фронтенд: маршруты `/`, `/profile`, `/u/:identifier`, Telegram UI, клиент API с cookie-сессией.
- Опубликовано `docs/features/profile-and-public-profiles.md`.
