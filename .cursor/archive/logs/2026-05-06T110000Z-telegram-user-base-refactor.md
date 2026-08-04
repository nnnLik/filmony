# 2026-05-06T11:00:00Z

- Feature slug: `telegram-user-base`
- Action type: refactor
- Summary: Убрано затенение `BaseSettings.schema`: поле переименовано в `default_schema`, env остаётся `DATABASE_SCHEMA`; правка `core/database.py`.
- Files:
  - `backend/src/conf/settings.py`
  - `backend/src/core/database.py`
- Verification: предупреждение Pydantic при старте Uvicorn не воспроизводится (логи Docker).
