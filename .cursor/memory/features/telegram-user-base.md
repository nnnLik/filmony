# Memory: telegram-user-base

- Сессия: JWT в httpOnly cookie, имя cookie из `AUTH_JWT_*` / defaults в `conf/settings.py`.
- Pytest: `src/tests/conftest.py` выставляет `ENV=test`; движок подключается к базе из `DATABASE_TEST_URL`.
- Таблица пользователя: имя `user` (генерация из `Base` + `to_snake_case`).
- Полный чеклист фичи: `.cursor/features/001-telegram-user-base.md`; артефакты доставки: `.cursor/active/telegram-user-base/`, `docs/features/telegram-user-base.md`.
