# Result — user-subscriptions

## Feature
- Slug: `user-subscriptions`
- Final status: **in_progress** (код и тесты добавлены; запуск backend-команд в этой сессии не выполнен)

## Implemented
- Добавлена directed-модель подписки `UserSubscription`.
- Добавлена миграция `3c5f09189f9f_add_user_subscriptions.py` с:
  - FK на `user.id`
  - уникальной парой `(follower_user_id, following_user_id)`
  - check `follower_user_id <> following_user_id`
  - индексами по обоим FK.
- Реализованы сервисы создания, удаления и листинга подписок.
- Реализованы endpoints:
  - `POST /api/users/{user_id}/subscriptions`
  - `DELETE /api/users/{user_id}/subscriptions`
  - `GET /api/users/{user_id}/subscriptions?type=followers|following|both`
- Для `type=both` реализован плоский список элементов с `relation_type`.

## Changed Files
- `backend/src/models/user_subscription.py`
- `backend/src/models/__init__.py`
- `backend/src/migrations/versions/3c5f09189f9f_add_user_subscriptions.py`
- `backend/src/services/subscriptions/__init__.py`
- `backend/src/services/subscriptions/create_user_subscription.py`
- `backend/src/services/subscriptions/delete_user_subscription.py`
- `backend/src/services/subscriptions/list_user_subscriptions.py`
- `backend/src/api/profile/schemas.py`
- `backend/src/api/profile/users_routes.py`
- `backend/src/tests/api/test_profile_routes.py`
- `.cursor/features/user-subscriptions/feature.md`
- `.cursor/active/user-subscriptions/plan.md`
- `.cursor/active/user-subscriptions/progress.md`
- `.cursor/active/user-subscriptions/result.md`

## Verification
- IDE lints (`ReadLints`) on changed backend files: **no errors**.
- Команды Docker-first, которые нужно выполнить локально:
  - `make backend-test-one target=src/tests/api/test_profile_routes.py`
  - `make backend-test`
  - `make backend-lint`

## Known Limitations
- Поле `friends_count` в профиле не мигрировано в `followers/following` в рамках этой задачи, чтобы не ломать существующий контракт фронта.
