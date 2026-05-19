# Telegram engagement notifications

## Summary

- **Шаринг карточки:** автор отправляет уведомление **своим подписчикам** (followers): только пользователи из отношения `UserSubscription`, где `following_user_id` = автор и `follower_user_id` ∈ списка получателей. Это **не** список «мои подписки» (following).
- **Авто-уведомления подписчикам при публикации:** новая карточка или новый пост ленты — см. [`followed-content-notifications.md`](./followed-content-notifications.md) (для постов без дубля с @упоминаниями).
- **Реакции и комментарии:** при добавлении реакции на карточку или комментарий, при ответе на комментарий и при корневом комментарии под карточкой — соответствующие DM в Telegram (см. каноничный документ [`engagement-telegram-notifications.md`](./engagement-telegram-notifications.md)).

## User flows

1. **Share карточки**  
   Автор после создания (шаг 5 wizard) или с экрана «Поделиться» выбирает одного или нескольких **подписчиков** → `POST /api/cards/{card_id}/share` с телом `{"recipient_user_ids": ["<uuid>", ...]}` (до 100) → для каждого получателя ставится задача Celery `tasks.telegram_engagement.deliver_shared_movie_card`.

2. **Реакция на карточку**  
   Пользователь ставит реакцию на чужую карточку → владелец карточки получает DM (если не self-react). Реализовано.

3. **Реакция на комментарий**  
   Аналогично для автора комментария. Реализовано.

4. **Ответ на комментарий / новый корневой комментарий**  
   См. [`engagement-telegram-notifications.md`](./engagement-telegram-notifications.md).

## Message format (Telegram)

- Текст: действие + имя инициатора + ссылка «Открыть в Filmony» (`https://t.me/<bot>/app?startapp=c<card_id>` и др.).
- Для шаринга при необходимости отправляется фото постера (если настроено в сервисе доставки).

## Правила и защита

- Получатели share — только **подписчики** автора карточки; не себе; дубликаты в запросе допустимы и нормализуются до уникальных UUID.
- Dedupe / rate limits — по политике сервисов доставки и задач (см. код `engagement_delivery`, настройки).
- Ошибки Telegram **не ломают** HTTP-ответ основного API; пишутся в лог.

## Важные ограничения

- Получатель должен иметь **начатый диалог с ботом** (`/start`), иначе личное сообщение может быть недоступно.
- Исходящая доставка share и engagement — **асинхронно через Celery**, не в теле ответа `POST /share`.

## API (реализованный контракт)

| Метод | Путь | Тело / ответ |
|--------|------|----------------|
| POST | `/api/cards/{card_id}/share` | `{ "recipient_user_ids": ["uuid", ...] }` → `{ "queued": <int> }` |

Ошибки: `401`, `403` (не владелец карточки), `404` (нет карточки), `422` (нет получателей, слишком много, или не все — подписчики автора).

## Статус MVP

- Share + инфраструктура Celery — **готово**.
- Уведомления по реакциям и комментариям — **готово** (см. [`engagement-telegram-notifications.md`](./engagement-telegram-notifications.md)).
- Авто-уведомления подписчикам о **новой карточке** и **новом посте ленты** — **готово** (см. [`followed-content-notifications.md`](./followed-content-notifications.md); посты: без дубля для @упоминаний).

## References

- `.cursor/features/telegram-engagement-notifications/feature.md`
- `.cursor/features/followed-content-notifications/feature.md`
- Расширенный бэклог бота: `.cursor/features/009-telegram-notifications.md`
