---
name: backend subscriptions system
overview: Добавить directed-подписки (follower -> following) на бэкенде и новый endpoint получения подписчиков/подписок/обоих по query-параметру в плоском формате.
todos:
  - id: contracts
    content: Зафиксировать API-контракт subscriptions и response-схемы (flat-list + relation_type).
    status: completed
  - id: db-model-migration
    content: Добавить модель UserSubscription и Alembic-миграцию с unique/index constraints.
    status: completed
  - id: services
    content: Реализовать Create/Delete/List сервисы подписок в отдельном домене services/subscriptions.
    status: completed
  - id: routes
    content: Добавить POST/DELETE/GET subscriptions routes в users_routes.py с корректной HTTP-мэппинг-обработкой ошибок.
    status: completed
  - id: tests
    content: Покрыть subscriptions API-тестами для followers/following/both и error-cases.
    status: completed
  - id: feature-artifacts
    content: Обновить обязательные feature-артефакты и action-log по workflow-правилам.
    status: completed
isProject: false
---

# Backend Subscriptions Plan

## Подтверждённые требования
- Подписки асимметричные: пользователь может подписываться на неограниченное число других пользователей.
- На пользователя может подписаться неограниченное число других пользователей.
- Списки нужны для любого `user_id`.
- Один endpoint с query-параметром `type` (`followers | following | both`).
- Для `both` формат ответа — **плоский список** с признаком типа связи в каждом элементе.

## Точки интеграции в текущем коде
- API профилей пользователей: [`backend/src/api/profile/users_routes.py`](backend/src/api/profile/users_routes.py)
- Pydantic-схемы профиля/ответов: [`backend/src/api/profile/schemas.py`](backend/src/api/profile/schemas.py)
- Модель пользователя: [`backend/src/models/user.py`](backend/src/models/user.py)
- Реэкспорт моделей для metadata: [`backend/src/models/__init__.py`](backend/src/models/__init__.py)
- Заглушка счётчиков профиля: [`backend/src/services/profile/get_user_profile_counts.py`](backend/src/services/profile/get_user_profile_counts.py)
- Тесты API профилей: [`backend/src/tests/api/test_profile_routes.py`](backend/src/tests/api/test_profile_routes.py)
- Миграции Alembic: [`backend/src/migrations/versions`](backend/src/migrations/versions)

## Предлагаемый API-контракт
- `POST /api/users/{user_id}/subscriptions`
  - Создаёт подписку текущего пользователя на `user_id`.
  - Ошибки: `404` (target не найден), `409` (уже подписан), `422` (self-subscribe).
- `DELETE /api/users/{user_id}/subscriptions`
  - Отписка текущего пользователя от `user_id`.
  - Ошибки: `404` (target не найден или подписка отсутствует — выбрать и зафиксировать единый вариант в реализации).
- `GET /api/users/{user_id}/subscriptions?type=followers|following|both`
  - Возвращает плоский список связей.
  - При `both` объединяет follower/following записи в одном массиве.
  - Каждый элемент включает: пользователя, и `relation_type` (`follower` или `following`).

## Изменения по слоям

### 1) Data layer
- Добавить модель directed-подписки, например `UserSubscription` в [`backend/src/models/user_subscription.py`](backend/src/models/user_subscription.py):
  - `id` (UUID PK)
  - `follower_user_id` (FK -> `user.id`, index)
  - `following_user_id` (FK -> `user.id`, index)
  - `created_at`
  - `UniqueConstraint(follower_user_id, following_user_id)`
  - check/валидация против self-subscribe
- Подключить модель в [`backend/src/models/__init__.py`](backend/src/models/__init__.py).
- Создать миграцию в [`backend/src/migrations/versions`](backend/src/migrations/versions) для таблицы подписок и индексов.

### 2) Service layer (по стандарту один сервис = одна задача)
- Добавить сервисы в `backend/src/services/subscriptions/`:
  - `CreateUserSubscriptionService.execute(viewer_id, target_user_id)`
  - `DeleteUserSubscriptionService.execute(viewer_id, target_user_id)`
  - `ListUserSubscriptionsService.execute(target_user_id, relation_filter)`
- Для list-сервиса вернуть typed DTO (dataclass), без сырого dict.
- Проверку существования target-user делать явно (через существующий сервис/репозиторный запрос), ошибки маппить в route layer.

### 3) API + схемы
- В [`backend/src/api/profile/schemas.py`](backend/src/api/profile/schemas.py) добавить:
  - enum для query-параметра (`followers`, `following`, `both`)
  - `SubscriptionListItemResponse` (поля пользователя + `relation_type`)
  - `SubscriptionListResponse` с `items: list[SubscriptionListItemResponse]`
- В [`backend/src/api/profile/users_routes.py`](backend/src/api/profile/users_routes.py) добавить 3 endpoint’а (`POST/DELETE/GET`), используя `CurrentUser` и `AsyncSession` по текущему паттерну.

### 4) Профильные счётчики
- Расширить [`backend/src/services/profile/get_user_profile_counts.py`](backend/src/services/profile/get_user_profile_counts.py):
  - либо заменить `friends` на более релевантные `followers`/`following`,
  - либо временно оставить обратную совместимость и дополнить без удаления текущего `friends_count`.
- Минимизировать breaking changes: не ломать существующие ответы профилей, если фронт ещё ждёт `friends_count`.

### 5) Тесты
- Расширить [`backend/src/tests/api/test_profile_routes.py`](backend/src/tests/api/test_profile_routes.py) или вынести в отдельный `test_subscriptions_routes.py`:
  - create subscription happy path
  - duplicate subscribe -> `409`
  - self-subscribe -> `422`
  - unsubscribe happy path
  - list `type=followers`
  - list `type=following`
  - list `type=both` -> плоский список с двумя `relation_type`
  - unknown `user_id` -> `404`
  - unauthorized -> `401`
- Запуск в Docker: `make backend-test-one target=...` и затем `make backend-test`.

### 6) Обязательные артефакты фичи (по правилам workspace)
- Создать/обновить:
  - `.cursor/active/<feature-slug>/plan.md`
  - `.cursor/active/<feature-slug>/progress.md`
  - `.cursor/active/<feature-slug>/result.md`
  - `docs/features/<feature-slug>.md`
  - `.cursor/memory/logs/action-log.md`

## Поток данных
```mermaid
flowchart LR
viewer[CurrentUser] --> postRoute[POST_or_DELETE_/api/users/{user_id}/subscriptions]
viewer --> listRoute[GET_/api/users/{user_id}/subscriptions?type=...]
postRoute --> createDeleteService[Create_or_Delete_Subscription_Service]
listRoute --> listService[List_Subscriptions_Service]
createDeleteService --> subTable[(user_subscription)]
listService --> subTable
listService --> userTable[(user)]
userTable --> apiResp[flat_items_with_relation_type]
subTable --> apiResp
```

## Риски и решения
- Большие списки подписок: сразу заложить сортировку (по `created_at DESC`) и расширяемую структуру под будущую пагинацию.
- Совместимость с текущим `friends_count`: сохранить поле до отдельной миграции фронта, чтобы избежать регрессий.
- Дубликаты в `both`: объединять два набора без дублей по `(relation_type, user_id)`.
