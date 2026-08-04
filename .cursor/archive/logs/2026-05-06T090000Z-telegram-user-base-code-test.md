# 2026-05-06T09:00:00Z

- Feature slug: `telegram-user-base`
- Action type: code | test
- Summary: Auth API (initData, JWT cookie), User model, Alembic migration, pytest `test_telegram_auth`, compose Postgres, Makefile.
- Files:
  - `backend/src/api/auth/routes.py`
  - `backend/src/api/auth/schemas.py`
  - `backend/src/api/router.py`
  - `backend/src/deps/auth.py`
  - `backend/src/services/auth/*`
  - `backend/src/models/user.py`
  - `backend/src/migrations/versions/001_users.py`
  - `backend/src/tests/test_telegram_auth.py`
  - `compose.yml`
  - `Makefile`
- Verification: `make backend-test` (Docker-first).
