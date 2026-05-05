# Memory: telegram-user-base

- Сессия: JWT в httpOnly cookie, имя cookie из `AUTH_JWT_*` / defaults в `conf/settings.py`.
- Pytest: первые строки `src/tests/conftest.py` выставляют `ENV=test`; движок использует `DATABASE_TEST_SCHEMA` в `search_path`.
- Таблица пользователя: имя `user` (генерация из `Base` + `to_snake_case`).
- Полный чеклист фичи: `.cursor/features/001-telegram-user-base.md`; артефакты доставки: `.cursor/active/telegram-user-base/`, `docs/features/telegram-user-base.md`.
