# Feature: profile-and-public-profiles

## Metadata
- Feature slug: `profile-and-public-profiles`
- Source backlog: [`.cursor/features/002-profile-and-public-profiles.md`](../../features/002-profile-and-public-profiles.md)
- Priority: P1
- Target area: fullstack
- Depends on: `telegram-user-base` (001)

## Problem
После авторизации нужны идентичность и обнаруживаемость: свой редактируемый профиль и просмотр чужих профилей с пагинируемым списком карточек фильмов (до появления данных — пустой контракт).

## Scope
- In scope: API `GET/PATCH /api/me/profile`, публичные `GET /api/users/...`, пустая пагинация карточек; экраны «Мой профиль» и чужой `/u/:identifier`; сессия через существующий cookie после `POST /api/auth/telegram`.
- Out of scope: Redis-кеш (опционально позже), друзья/приватность сложнее 404, реальные строки `movie_cards`.

## Functional Requirements
- [x] Свой профиль: чтение и сохранение `display_name`, `bio`, `profile_slug` с валидацией.
- [x] Чужой профиль по UUID или slug (авторизованный зритель); несуществующий пользователь — 404.
- [x] Список карточек: контракт пагинации, v1 — пустой массив.

## Acceptance Criteria
- [x] Авторизованный пользователь открывает свой профиль и сохраняет правки; ошибки валидации отображаются.
- [x] Любой авторизованный пользователь открывает чужой профиль по стабильному идентификатору и видит пустой список карточек с корректным контрактом.
- [x] Несуществующий пользователь — 404 (модель приватности зафиксирована в описании API).
- [x] Список поддерживает «загрузить ещё» (кнопка; при пустых данных курсор `null`).

## Constraints
- Docker-first для бэкенд-тестов и миграций (см. `.cursor/tech.md`).
- Сервисы с одним публичным методом `execute`, UI на `@telegram-apps/telegram-ui`.

## References
- [`.cursor/user-story.md`](../../user-story.md) — ручной поиск по профилям.
- [`docs/features/profile-and-public-profiles.md`](../../../docs/features/profile-and-public-profiles.md)
