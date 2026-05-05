# Telegram user (database foundation)

Источник требований также в [../001-telegram-user-base.md](../001-telegram-user-base.md) (тот же смысл, slug `telegram-user-base`).

## Metadata

| Field | Value |
|--------|--------|
| **Feature slug** | `telegram-user-base` |
| **Priority** | P0 |
| **Target area** | fullstack |

## Summary

Доверенная идентичность для Mini App: проверка Telegram `initData`, upsert пользователя по `telegram_user_id`, сессия (JWT в httpOnly cookie), `GET /api/me` с зависимостью текущего пользователя.

## Acceptance criteria

- [ ] Сервер отклоняет невалидный или просроченный `initData` с 401, пользователь не создаётся.
- [ ] Валидный `initData` создаёт/обновляет пользователя; повторные вызовы идемпотентны.
- [ ] Защищённый `GET /api/me` отдаёт пользователя только при валидной сессии.
- [ ] В TMA вход без ручных шагов; вне TMA — понятное сообщение.
- [ ] Секреты только из env / `vars`, не в репозитории.

## Out of scope

См. исходный документ 001 (email/password, полный профиль UI — 002).
