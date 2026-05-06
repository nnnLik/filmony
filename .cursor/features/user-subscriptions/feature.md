# Feature: user-subscriptions

## Problem
Пользователи не могут подписываться друг на друга и получать списки подписчиков/подписок.

## Scope
- Directed subscriptions (`follower -> following`) без лимитов по количеству.
- API для подписки/отписки.
- API для списка подписчиков/подписок/обоих по query-параметру.

## API Contract
- `POST /api/users/{user_id}/subscriptions`
  - Создает подписку текущего пользователя на `user_id`.
  - Ошибки: `404` (пользователь не найден), `409` (подписка уже существует), `422` (self-subscribe).
- `DELETE /api/users/{user_id}/subscriptions`
  - Удаляет подписку текущего пользователя на `user_id`.
  - Ошибки: `404` (пользователь не найден или подписка отсутствует).
- `GET /api/users/{user_id}/subscriptions?type=followers|following|both`
  - Возвращает плоский список `items`.
  - Каждый элемент содержит публичные поля пользователя и `relation_type` (`follower` или `following`).

## Acceptance Criteria
1. В БД есть таблица подписок с уникальной парой `(follower_user_id, following_user_id)`.
2. Self-subscribe запрещен.
3. Endpoint списка корректно поддерживает `type=followers`, `type=following`, `type=both`.
4. Добавлены API-тесты happy-path и ошибок (`401/404/409/422`).
