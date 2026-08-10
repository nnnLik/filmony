# Progress — standalone-web-telegram-login

**Status:** in_progress

## 2026-08-10 — Task 1 complete

- Scaffolding feature artifacts (feature.md, plan.md, design spec, HOT).
- Implemented `VerifyTelegramLoginWidgetService` TDD-style with unit tests.
- **Tests:** 6 passed (`src/tests/unit/auth/test_verify_telegram_login_widget.py`).
  - Host fallback (Docker unavailable): `PYTHONPATH=src python3.12 -m pytest src/tests/unit/auth/test_verify_telegram_login_widget.py -o addopts= --confcutdir=src/tests/unit/auth`
  - Docker target: `make backend-test-one target=src/tests/unit/auth/test_verify_telegram_login_widget.py`

## 2026-08-10 — Task 3 complete

- Replaced `AuthStatus` `skipped` with `unauthenticated`.
- Browser bootstrap runs resume probes then ends in `unauthenticated` (no initData / authTelegram).
- TMA bootstrap unchanged after failed resume (initData wait + authTelegram).
- `AuthProvider` always runs bootstrap; gates `signalTelegramWebAppReady` to TMA.
- Added `authTelegramWidget` API type + POST helper in `profileApi.ts`.
- `useAuthReadyGate`: `unauthenticated` is not pending.
- Page gates renamed `skipped` → `unauthenticated` (same UX text until LoginPage).
- **Tests:** 4 passed (`src/auth/authBootstrap.test.ts`); `npx tsc --noEmit` clean.
