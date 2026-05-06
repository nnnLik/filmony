# 2026-05-06T10:30:00Z

- Feature slug: `telegram-user-base`
- Action type: refactor
- Summary: Режим тестов через `ENV=test` и `DatabaseSettings`; убран глобальный `_testing`; DDL для pytest только в `src/tests/conftest.py`; PostgreSQL-only.
- Files:
  - `backend/src/conf/settings.py`
  - `backend/src/core/database.py`
  - `backend/src/tests/conftest.py`
- Verification: ожидается `make backend-test` в контейнере.
