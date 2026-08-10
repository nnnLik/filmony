# Progress — standalone-web-telegram-login

**Status:** in_progress

## 2026-08-10 — Task 1 complete

- Scaffolding feature artifacts (feature.md, plan.md, design spec, HOT).
- Implemented `VerifyTelegramLoginWidgetService` TDD-style with unit tests.
- **Tests:** 6 passed (`src/tests/unit/auth/test_verify_telegram_login_widget.py`).
  - Host fallback (Docker unavailable): `PYTHONPATH=src python3.12 -m pytest src/tests/unit/auth/test_verify_telegram_login_widget.py -o addopts= --confcutdir=src/tests/unit/auth`
  - Docker target: `make backend-test-one target=src/tests/unit/auth/test_verify_telegram_login_widget.py`

## 2026-08-10 — Task 2 complete

- Added `TelegramWidgetAuthRequest` schema and `POST /api/auth/telegram-widget` route.
- Route delegates HMAC verification to `VerifyTelegramLoginWidgetService`, then reuses upsert/JWT/cookie flow from `/telegram`.
- Integration tests in `src/tests/integration/auth/test_telegram_widget.py` (happy path, bad hash, missing hash 422, widget+initData same user).
