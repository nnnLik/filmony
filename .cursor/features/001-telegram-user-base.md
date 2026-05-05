# 001 — Telegram user (database foundation)

## Metadata

| Field | Value |
|--------|--------|
| **Feature slug** | `telegram-user-base` |
| **Priority** | P0 (blocking for all auth-dependent features) |
| **Target area** | fullstack |
| **Depends on** | — |
| **Unlocks** | 002–009 |

## Summary

Establish a **trusted identity** for each Mini App session: validate Telegram `initData`, upsert a **User** row (linked to `telegram_user_id`), and expose the current user to the frontend via API. This is the **base layer** for profiles, friends, cards, feed, and notifications described in [`.cursor/tech.md`](../tech.md) and [`.cursor/user-story.md`](../user-story.md).

## Problem

The frontend already reads `tgWebAppData.user` for display only (`frontend/src/App.tsx`). The backend must persist users and authenticate requests so every subsequent feature operates on a stable `user_id`, not on spoofable client-only fields.

## Backend

### Responsibilities

- Accept Telegram Mini App **initData** (header or body), verify **HMAC** with the bot token (Telegram login rules).
- Map Telegram user → internal **UUID/int PK**; store `telegram_user_id`, optional `username`, `first_name`, `last_name`, `photo_url`/`language_code` if needed for UX.
- Issue **session** strategy agreed by the team: signed JWT in httpOnly cookie, or short-lived token + refresh — document in implementation plan.
- Middleware / dependency: **`get_current_user`** for protected routes.
- Optional: webhook-ready **bot token** configuration in settings (used later by 009).

### Data model (planned)

- Table **`users`**: primary key, `telegram_user_id` **unique**, profile fields, `created_at`, `updated_at`.
- Index on `telegram_user_id` for login path.

### API (planned)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/auth/telegram` | Body: `initData` string → verify → upsert user → session |
| `GET` | `/api/me` | Current user profile (requires auth) |
| `POST` | `/api/auth/logout` | Invalidate session (if applicable) |

OpenAPI: extend via FastAPI routers under prefix `/api` (see existing [`backend/src/api/router.py`](../../backend/src/api/router.py)).

### Configuration

- Extend [`backend/src/conf/settings.py`](../../backend/src/conf/settings.py): `TELEGRAM_BOT_TOKEN`, optional `TELEGRAM_BOT_USERNAME`, DB URL when PostgreSQL is wired.

### Integrations

- **Telegram**: [Web Apps — validating data](https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app) (hash verification).

### Celery / Redis

- Not required for MVP of this feature; session can live in DB or signed JWT only.

### Existing codebase references

| File | Role today |
|------|------------|
| [`backend/src/main.py`](../../backend/src/main.py) | FastAPI app entry, mounts routers via `setup_app` |
| [`backend/src/utils/app_utils.py`](../../backend/src/utils/app_utils.py) | CORS, includes `api_router` |
| [`backend/src/api/router.py`](../../backend/src/api/router.py) | API prefix `/api`; add auth routes here or sub-router |
| [`backend/src/conf/settings.py`](../../backend/src/conf/settings.py) | `DatabaseSettings` placeholder — fill when DB added |

### Suggested new modules (implementation)

- `backend/src/api/auth/` — routes, schemas (`TelegramAuthRequest`, `UserResponse`).
- `backend/src/services/auth/telegram_init_data.py` — hash verification.
- `backend/src/models/user.py` — SQLAlchemy / SQLModel model (once ORM is chosen).
- `backend/src/deps/auth.py` — `CurrentUser` dependency.

## Frontend

### Responsibilities

- On Mini App load, read **`initData`** via `@telegram-apps/sdk` / bridge (same stack as [`frontend/src/App.tsx`](../../frontend/src/App.tsx)).
- **POST** `initData` to `/api/auth/telegram` (proxied by Vite — [`frontend/vite.config.ts`](../../frontend/vite.config.ts).
- Store session handling per backend contract (cookie automatic with `credentials: 'include'` if cookie-based).
- Centralize API client (fetch wrapper with base URL, errors) for reuse in 002–009.

### UX

- Loading / error states for “вход не выполнен”.
- Respect theme (`isMiniAppDark`) for auth errors — consistent with current layout patterns in `App.tsx`.

### Existing codebase references

| File | Role |
|------|------|
| [`frontend/src/App.tsx`](../../frontend/src/App.tsx) | `useLaunchParams`, `tgWebAppData.user` — extend with auth exchange |
| [`frontend/src/main.tsx`](../../frontend/src/main.tsx) | App bootstrap |
| [`frontend/vite.config.ts`](../../frontend/vite.config.ts) | Proxy `/api` → backend |
| [`frontend/src/types/telegram/window-telegram.d.ts`](../../frontend/src/types/telegram/window-telegram.d.ts) | Telegram typings |

### Suggested new files

- `frontend/src/api/client.ts` — authenticated fetch.
- `frontend/src/hooks/useTelegramAuth.ts` — initData → `/api/auth/telegram`.
- `frontend/src/context/AuthContext.tsx` — current user + loading.

## Acceptance criteria

- [ ] Server rejects invalid or expired `initData` with 401 and does not create a user.
- [ ] Valid `initData` creates or updates a user; repeated calls are idempotent for the same Telegram account.
- [ ] Protected endpoint (e.g. `GET /api/me`) returns the persisted user only when authenticated.
- [ ] Frontend in TMA completes login without manual steps; outside TMA shows a clear message (reuse pattern from `OutsideTelegramPanel` in `App.tsx`).
- [ ] Secrets (bot token) are read from environment / `vars`, not committed.

## Out of scope

- Email/password login, OAuth providers other than Telegram.
- Full profile editing UI (covered in **002**).

## References

- [`.cursor/README.md`](../README.md) — feature workflow (`feature.md` under slug folder when implementing).
- [`.cursor/tech.md`](../tech.md) — stack, Telegram Mini App, FastAPI.
