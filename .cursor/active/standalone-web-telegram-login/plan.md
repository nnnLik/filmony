# Plan — standalone-web-telegram-login

## Task 1 — Widget verifier service (current)

1. Add `TelegramLoginWidgetInvalidError` to `services/auth/errors.py`.
2. Implement `VerifyTelegramLoginWidgetService` in `services/auth/verify_telegram_login_widget.py` (mirror `VerifyTelegramInitDataService` ctor style).
3. Add test signer `tests/auth/telegram_login_widget.py`.
4. Unit tests at `tests/unit/auth/test_verify_telegram_login_widget.py`.

## Task 2 — Auth route (later)

1. `POST /api/auth/telegram/widget` — parse body, call verifier, upsert user, issue session.
2. Integration tests in `tests/integration/auth/`.

## Task 3 — Frontend (later)

1. Detect standalone vs TMA.
2. Render Login Widget; POST callback to widget endpoint.
3. Lint + build.
