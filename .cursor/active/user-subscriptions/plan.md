# Implementation Plan — user-subscriptions

## Feature
- Slug: `user-subscriptions`
- Source spec: `.cursor/features/user-subscriptions/feature.md`

## Goal
Добавить directed-подписки между пользователями и единый endpoint для выборки `followers/following/both` в плоском формате.

## Step-by-Step Plan
1. Data layer: модель `UserSubscription` + миграция с `UniqueConstraint` и check на self-subscribe.
2. Service layer: отдельные сервисы для create/delete/list.
3. API layer: `POST/DELETE/GET /api/users/{user_id}/subscriptions`.
4. Tests: расширение `backend/src/tests/api/test_profile_routes.py`.
5. Docs/workflow: обновление active/result/docs/action-log артефактов.

## Verification Plan
- `make backend-test-one target=src/tests/api/test_profile_routes.py`
- `make backend-test`
- `make backend-lint`
