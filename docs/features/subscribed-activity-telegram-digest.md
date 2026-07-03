# Telegram Digest Подписанной Активности

## Summary

Раз в **48 часов** пользователи с активной Telegram-связкой и хотя бы одной подпиской могут получить компактный DM с **до 3 инсайтами** об активности людей, на которых они подписаны. Digest не заменяет точечные уведомления о публикациях.

## Celery task

| Task | Назначение |
|------|------------|
| `tasks.telegram_engagement.send_subscribed_activity_digests` | Batch: найти due recipients, собрать и отправить digest |

Расписание beat настраивается в deployment (в `celery_app.py` beat не включён).

## Источники инсайтов

- новые user cards подписанных авторов;
- новые feed posts;
- высокие оценки (≥9);
- сводный сигнал по автору (≥2 события за окно).

Выбор **3 пунктов** — weighted random из scored pool с ограничениями: max 1 пункт на автора, max 2 одного типа.

## Связанный код

- [`send_subscribed_activity_digest.py`](../../backend/src/services/telegram/send_subscribed_activity_digest.py)
- [`subscribed_activity_digest_candidates.py`](../../backend/src/services/telegram/subscribed_activity_digest_candidates.py)
- [`subscribed_activity_digest_state.py`](../../backend/src/models/subscribed_activity_digest_state.py)
- [`telegram_engagement.py`](../../backend/src/tasks/telegram_engagement.py)

## Tests

- `backend/src/tests/services/telegram/test_subscribed_activity_digest.py`
- `backend/src/tests/tasks/test_subscribed_activity_digest.py`
- `backend/src/tests/services/subscriptions/test_list_following_user_ids_for_follower_user.py`
