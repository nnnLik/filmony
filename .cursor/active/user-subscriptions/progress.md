# Progress — user-subscriptions

## Status
- **done**

## Log
- Добавлена модель `UserSubscription` и миграция `3c5f09189f9f_add_user_subscriptions.py`.
- Добавлены сервисы:
  - `CreateUserSubscriptionService`
  - `DeleteUserSubscriptionService`
  - `ListUserSubscriptionsService`
- Добавлены API endpoints:
  - `POST /api/users/{user_id}/subscriptions`
  - `DELETE /api/users/{user_id}/subscriptions`
  - `GET /api/users/{user_id}/subscriptions?type=...`
- Добавлены response-схемы для плоского списка подписок.
- Расширены API-тесты в `backend/src/tests/api/test_profile_routes.py`.
- Линтер проверен через IDE diagnostics: ошибок в измененных файлах нет.
- Запуск shell-команд в текущей сессии был отклонен (`User chose to skip`), поэтому прогон `make backend-test*` не выполнен в этой сессии.
- Closeout по подтверждению пользователя: задача считается завершённой, дополнительная работа не требуется.
