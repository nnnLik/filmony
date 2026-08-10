# Standalone Web + Telegram Login Widget — Design Spec

**Date:** 2026-08-10  
**Status:** approved  
**Feature slug:** `standalone-web-telegram-login`

---

## 1. Context

Filmony today authenticates users via Telegram Mini App `initData` (HMAC with `WebAppData` key). Outside the TMA shell (standalone browser), users cannot sign in.

Telegram provides a [Login Widget](https://core.telegram.org/widgets/login) that returns flat user fields (`id`, `auth_date`, `hash`, optional profile fields) signed with a different algorithm: `secret_key = SHA256(bot_token)` (not `HMAC-WebAppData`).

---

## 2. Goals

- Allow sign-in from a standalone web page using the Telegram Login Widget.
- Reuse existing session issuance (`IssueSessionJwtService`) and user upsert after verification.
- Keep Mini App `initData` flow unchanged.
- Reject invalid, tampered, or expired widget payloads with 401.

---

## 3. Architecture

### 3.1 Backend

| Component | Responsibility |
|-----------|----------------|
| `VerifyTelegramLoginWidgetService` | Validate widget HMAC, `auth_date` freshness, return `TelegramWebAppUser` |
| `TelegramLoginWidgetInvalidError` | Typed failure for invalid widget payloads |
| `POST /api/auth/telegram/widget` (later slice) | Parse body → verify → upsert user → issue session cookie |

**Widget verification algorithm:**

1. Require `hash` and `auth_date`; reject if `auth_date` older than `max_age_seconds` (default 86400) or in the future (+60s skew).
2. Build `data_check_string` from sorted `key=value` lines for all received fields **except** `hash`.
3. `secret_key = SHA256(bot_token)` (raw digest bytes).
4. `calculated_hash = HMAC-SHA256(secret_key, data_check_string).hexdigest()`.
5. Constant-time compare with received `hash`.
6. Map `id` → `telegram_user_id`; `language_code=None` (widget does not send it).

### 3.2 Frontend (later slice)

- Detect standalone vs TMA (`window.Telegram?.WebApp`).
- Render Telegram Login Widget on login page when not in TMA.
- POST widget callback payload to new auth endpoint; redirect on success.

### 3.3 Out of scope (this slice)

- HTTP route and upsert wiring.
- Frontend widget integration.
- Changes to `VerifyTelegramInitDataService`.

---

## 4. API contract (planned)

```http
POST /api/auth/telegram/widget
Content-Type: application/json

{
  "id": 123456789,
  "auth_date": 1699999999,
  "hash": "...",
  "first_name": "Test",
  "username": "tester"
}

200 OK + Set-Cookie session   — valid widget, user upserted
401 Unauthorized              — invalid hash, missing fields, or expired auth_date
```

---

## 5. Testing

### Unit (`tests/unit/auth/`)

- Valid signature → `TelegramWebAppUser`
- Wrong hash → `TelegramLoginWidgetInvalidError`
- Expired `auth_date` → error
- Missing `hash` / `auth_date` → error
- Field-order independence (signer builds payload in arbitrary order)

### Integration (later slice)

- `POST /api/auth/telegram/widget` happy path, 401 cases, cookie + `/api/me`

### Frontend (later slice)

- Lint + build on touched login components

---

## 6. Acceptance criteria

- [ ] `VerifyTelegramLoginWidgetService` validates widget payloads per Telegram Login Widget rules.
- [ ] Invalid or expired payloads raise `TelegramLoginWidgetInvalidError`.
- [ ] Unit tests cover happy path and failure modes listed above.
- [ ] (Later) Standalone browser can sign in via widget; TMA flow unchanged.
- [ ] (Later) Secrets only from env / `vars`.

---

## 7. Security notes

- Same `max_age_seconds` default as initData verifier (24h).
- Constant-time HMAC comparison.
- Bot token never logged or returned to client.
