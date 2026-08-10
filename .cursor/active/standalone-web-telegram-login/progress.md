# Progress — standalone-web-telegram-login

**Status:** in_progress

## 2026-08-10 — Task 1 complete

- Scaffolding feature artifacts (feature.md, plan.md, design spec, HOT).
- Implemented `VerifyTelegramLoginWidgetService` TDD-style with unit tests.
- **Tests:** 6 passed (`src/tests/unit/auth/test_verify_telegram_login_widget.py`).
  - Host fallback (Docker unavailable): `PYTHONPATH=src python3.12 -m pytest src/tests/unit/auth/test_verify_telegram_login_widget.py -o addopts= --confcutdir=src/tests/unit/auth`
  - Docker target: `make backend-test-one target=src/tests/unit/auth/test_verify_telegram_login_widget.py`

## 2026-08-10 — Task 4 complete (frontend login page)

- Added `TelegramLoginWidget`, `LoginPage`, `RequireAuth`; wired `/login` route.
- `AuthProvider` exports `completeLogin` via `AuthActionsContext` / `useAuthActions`.
- Protected routes wrapped with `RequireAuth`; removed dead-end «Откройте в Telegram» gates.
- Public routes (`PublicProfilePage`, `FilmDetailPage`, `CatalogDetailPage`) allow logged-out view.
- **Verification:** `npx tsc --noEmit` clean; `npm run lint` on touched files.
