# Standalone web + Telegram Login Widget

Design: [docs/superpowers/specs/2026-08-10-standalone-web-telegram-login-design.md](../../../docs/superpowers/specs/2026-08-10-standalone-web-telegram-login-design.md)

## Metadata

| Field | Value |
|--------|--------|
| **Feature slug** | `standalone-web-telegram-login` |
| **Priority** | P1 |
| **Target area** | backend (this slice), fullstack (follow-up) |

## Summary

Enable authentication outside the Telegram Mini App via the [Telegram Login Widget](https://core.telegram.org/widgets/login). This slice delivers `VerifyTelegramLoginWidgetService` with unit tests; HTTP route and frontend widget integration follow in later slices.

## Acceptance criteria

- [ ] `VerifyTelegramLoginWidgetService` validates flat widget fields (`id`, `auth_date`, `hash`, optional profile fields) using `SHA256(bot_token)` secret key (not WebAppData HMAC).
- [ ] Missing `hash` or `auth_date`, expired `auth_date` (>86400s), or hash mismatch raise `TelegramLoginWidgetInvalidError`.
- [ ] Valid payload returns `TelegramWebAppUser` with `language_code=None`.
- [ ] Unit tests cover: valid signature, wrong hash, expired `auth_date`, missing fields, field-order independence.
- [ ] (Later) `POST /api/auth/telegram/widget` issues session cookie; TMA `initData` flow unchanged.
- [ ] (Later) Standalone web login page shows widget when not in TMA.

## Out of scope (this slice)

- HTTP route and user upsert wiring
- Frontend Login Widget UI
- Changes to `VerifyTelegramInitDataService`
