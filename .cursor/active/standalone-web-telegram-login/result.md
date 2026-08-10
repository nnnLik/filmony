# Standalone web + Telegram Login Widget — result

**Date:** 2026-08-10  
**Status:** complete

## Implemented

- `VerifyTelegramLoginWidgetService` with `TelegramLoginWidgetInvalidError` (widget HMAC, `auth_date` window, constant-time compare).
- `POST /api/auth/telegram-widget` — parse body → verify → `UpsertTelegramUserService` → session cookie + `access_token` (mirrors TMA `/api/auth/telegram` path).
- Unit tests for verifier (happy path, wrong hash, expired/missing fields, field-order independence).
- Integration tests for widget route (cookie, `/api/me`, 401 cases, same user as initData).
- Frontend: `TelegramLoginWidget`, `LoginPage` at `/login`, `RequireAuth` on protected routes.
- `AuthProvider` / `authBootstrap`: browser → `unauthenticated` without initData; `completeLogin` via `AuthActionsContext`.
- Public routes (`PublicProfilePage`, `FilmDetailPage`, `CatalogDetailPage`) remain accessible when logged out; removed dead-end «Откройте в Telegram» gates.

## Changed files (summary)

| Area | Files |
|------|-------|
| Backend service | `backend/src/services/auth/verify_telegram_login_widget.py`, `backend/src/services/auth/errors.py` |
| API | `backend/src/api/auth/routes.py`, `backend/src/api/auth/schemas.py` |
| Tests | `backend/src/tests/unit/auth/test_verify_telegram_login_widget.py`, `backend/src/tests/integration/auth/test_telegram_widget.py`, `backend/src/tests/auth/telegram_login_widget.py` |
| Frontend auth | `frontend/src/auth/AuthProvider.tsx`, `frontend/src/auth/authBootstrap.ts`, `frontend/src/auth/RequireAuth.tsx`, `frontend/src/auth/auth-actions-context.ts`, `frontend/src/auth/useAuthActions.ts` |
| Frontend UI | `frontend/src/components/auth/TelegramLoginWidget.tsx`, `frontend/src/pages/LoginPage.tsx`, `frontend/src/routes.tsx` |
| API client | `frontend/src/api/profileApi.ts` |
| Env types | `frontend/src/vite-env.d.ts` |
| Artifacts | `.cursor/features/standalone-web-telegram-login/feature.md`, `.cursor/active/standalone-web-telegram-login/*`, `docs/superpowers/specs/2026-08-10-standalone-web-telegram-login-design.md` |

## Verification

```bash
# Unit — 6 passed (host fallback, Docker unavailable in closeout env)
PYTHONPATH=src python3.12 -m pytest src/tests/unit/auth/test_verify_telegram_login_widget.py -o addopts= --confcutdir=src/tests/unit/auth

# Integration — requires Docker + Postgres (not run in closeout env)
make backend-test-one target=src/tests/integration/auth/test_telegram_widget.py

# Frontend
cd frontend && npx tsc --noEmit   # clean
cd frontend && npm run lint       # clean on touched files
```

## Known limitations

- **BotFather domain:** Login Widget fails until the bot’s allowed domain includes the page origin (`/setdomain` per hostname; see `docs/features/standalone-web-telegram-login.md`).
- **Integration tests:** Written and wired; not executed in the closeout environment (Docker/Postgres required).
- **Local without Caddy:** Bare `localhost` is not accepted by Telegram; use `filmony.localhost` or a tunnel domain registered in BotFather.

## Next steps

- Manual smoke: widget login on staging/prod origin after `/setdomain`.
- Optional: E2E or Playwright for `/login` redirect + widget callback (out of scope for this slice).
