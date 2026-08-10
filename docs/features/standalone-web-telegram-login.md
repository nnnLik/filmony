# Standalone web + Telegram Login Widget

Sign-in for Filmony outside the Telegram Mini App (TMA) shell via the [Telegram Login Widget](https://core.telegram.org/widgets/login). TMA `initData` authentication is unchanged.

**Design spec:** `docs/superpowers/specs/2026-08-10-standalone-web-telegram-login-design.md`

## What shipped

| Layer | Deliverable |
|-------|-------------|
| Backend | `VerifyTelegramLoginWidgetService` — widget HMAC (`SHA256(bot_token)` secret), `auth_date` freshness |
| Backend | `POST /api/auth/telegram-widget` — verify → upsert user → session cookie + `access_token` |
| Backend | Unit tests (verifier) + integration tests (route, cookie, `/api/me`, initData parity) |
| Frontend | `/login` with `TelegramLoginWidget`, `RequireAuth` gate on protected routes |
| Frontend | Browser bootstrap → `unauthenticated` → login page; TMA bootstrap → `initData` flow as before |

## How authentication works

### Telegram Mini App (TMA)

1. `AuthProvider` detects `isTMA()` → environment `tma`.
2. `authBootstrap` waits for `initData`, then `POST /api/auth/telegram` with the raw string.
3. Backend: `VerifyTelegramInitDataService` (HMAC with `WebAppData` key) → `UpsertTelegramUserService` → `IssueSessionJwtService`.
4. Client stores `access_token` in session storage and sets auth session flag; protected routes render when `kind === 'ready'`.

### Standalone browser

1. `AuthProvider` → environment `browser`; no `initData` wait.
2. Resume probes (`Bearer` token, cookie `/api/me/profile`) fail → `kind: 'unauthenticated'`.
3. `RequireAuth` redirects to `/login?returnTo=…`.
4. `LoginPage` loads `telegram-widget.js` for `VITE_TELEGRAM_BOT_USERNAME`; user approves in Telegram.
5. Widget callback → `POST /api/auth/telegram-widget` with flat fields (`id`, `auth_date`, `hash`, optional profile fields).
6. Backend: `VerifyTelegramLoginWidgetService` → same upsert + session issuance as TMA.
7. `completeLogin()` → `ready`; user lands on `returnTo`.

Invalid, tampered, or expired widget payloads → **401** (`invalid telegram login widget data`). Missing required JSON fields → **422**.

## API

| Method | Path | Body | Success |
|--------|------|------|---------|
| POST | `/api/auth/telegram` | `{ "initData": "…" }` | 200 + Set-Cookie + `access_token` (TMA) |
| POST | `/api/auth/telegram-widget` | `{ "id", "auth_date", "hash", … }` | 200 + Set-Cookie + `access_token` (browser) |

## BotFather `/setdomain` checklist

The Login Widget only works on origins registered for the bot. In [@BotFather](https://t.me/BotFather): **Bot Settings → Domain** (`/setdomain`), then add **each hostname** where users open the web app (widget script runs on the **frontend page origin**, not the API host).

| Environment | Hostname to register | Notes |
|-------------|----------------------|--------|
| Local (Caddy dev) | `filmony.localhost` | `/etc/hosts` → `127.0.0.1`; see `docs/engineering/getting-started.md` |
| Local (direct Vite) | Dev machine hostname or tunnel domain | Telegram does not accept bare `localhost`; use Caddy vhost or ngrok/cloudflared and register that domain |
| Production | HTTPS origin of the deployed Filmony web app | Same host users open in the browser; set in deploy secrets (`VITE_API_ORIGIN` / frontend vhost) |

Also ensure **Menu Button / Mini App URL** still points at the TMA entry (separate from Login Widget domain rules).

Use the **same bot** as `TELEGRAM_BOT_TOKEN` / `TG_APP_TOKEN` on the backend and `VITE_TELEGRAM_BOT_USERNAME` on the frontend.

## Configuration

| Variable | Where | Purpose |
|----------|-------|---------|
| `VITE_TELEGRAM_BOT_USERNAME` | `vars/.env.development`, CI secrets | Bot username without `@` for widget `data-telegram-login` |
| `TELEGRAM_BOT_TOKEN` / `TG_APP_TOKEN` | Backend env | Widget HMAC and initData verification |
| `VITE_API_ORIGIN` | Frontend build | API base for `authTelegramWidget` |

Template: `vars/.env.example`.

## Key files

| Area | Path |
|------|------|
| Widget verifier | `backend/src/services/auth/verify_telegram_login_widget.py` |
| Typed error | `backend/src/services/auth/errors.py` |
| Auth routes | `backend/src/api/auth/routes.py` |
| Schemas | `backend/src/api/auth/schemas.py` |
| Unit tests | `backend/src/tests/unit/auth/test_verify_telegram_login_widget.py` |
| Integration tests | `backend/src/tests/integration/auth/test_telegram_widget.py` |
| Test signer | `backend/src/tests/auth/telegram_login_widget.py` |
| Widget UI | `frontend/src/components/auth/TelegramLoginWidget.tsx` |
| Login page | `frontend/src/pages/LoginPage.tsx` |
| Route guard | `frontend/src/auth/RequireAuth.tsx` |
| Bootstrap | `frontend/src/auth/authBootstrap.ts`, `frontend/src/auth/AuthProvider.tsx` |
| API client | `frontend/src/api/profileApi.ts` (`authTelegramWidget`) |
| Routes | `frontend/src/routes.tsx` (`/login`, `RequireAuth` wrappers) |

## Acceptance criteria

- [x] `VerifyTelegramLoginWidgetService` validates flat widget fields with `SHA256(bot_token)` HMAC (not WebAppData).
- [x] Missing `hash` / `auth_date`, expired `auth_date` (>86400s), or hash mismatch → `TelegramLoginWidgetInvalidError` / 401.
- [x] Valid payload → `TelegramWebAppUser` with `language_code=None`.
- [x] Unit tests: valid signature, wrong hash, expired `auth_date`, missing fields, field-order independence.
- [x] `POST /api/auth/telegram-widget` issues session cookie; widget and initData upsert the same user.
- [x] Standalone browser: `/login` + widget; TMA `initData` flow unchanged.
- [x] Protected routes use `RequireAuth`; public profile/film/catalog pages remain viewable when logged out.

## Verification

```bash
# Unit (host fallback when Docker unavailable)
PYTHONPATH=src python3.12 -m pytest src/tests/unit/auth/test_verify_telegram_login_widget.py -o addopts= --confcutdir=src/tests/unit/auth
# 6 passed

# Unit (Docker)
make backend-test-one target=src/tests/unit/auth/test_verify_telegram_login_widget.py

# Integration (Docker + Postgres)
make backend-test-one target=src/tests/integration/auth/test_telegram_widget.py

cd frontend && npx tsc --noEmit && npm run lint
```
