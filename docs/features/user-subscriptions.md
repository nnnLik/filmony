# Feature: user-subscriptions

## Назначение
Добавляет асимметричные подписки между пользователями и API для выборки подписчиков/подписок.

## API

| Метод | Путь | Описание |
|--------|------|----------|
| POST | `/api/users/{user_id}/subscriptions` | Подписаться на пользователя. |
| DELETE | `/api/users/{user_id}/subscriptions` | Отписаться от пользователя. |
| GET | `/api/users/{user_id}/subscriptions?type=followers|following|both` | Получить плоский список подписчиков/подписок/обоих. |

### Элемент ответа списка

```json
{
  "id": "uuid",
  "profile_slug": "u123...",
  "username": "optional",
  "first_name": "optional",
  "last_name": "optional",
  "photo_url": "optional",
  "display_name": "optional",
  "relation_type": "follower | following"
}
```

## Ошибки
- `401`: неавторизованный запрос.
- `404`: пользователь не найден (или подписка не найдена для delete).
- `409`: подписка уже существует.
- `422`: попытка подписки на самого себя.

## Хранилище
- Таблица: `user_subscription`.
- Ограничения:
  - уникальная пара `(follower_user_id, following_user_id)`;
  - check на запрет self-subscribe;
  - FK с `ON DELETE CASCADE`.

## Тесты
- Расширен `backend/src/tests/api/test_profile_routes.py` кейсами на:
  - create/delete subscription,
  - duplicate/self-subscribe errors,
  - list by `followers`/`following`/`both`,
  - `401` и `404`.
