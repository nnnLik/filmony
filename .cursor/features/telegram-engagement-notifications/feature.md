# Feature Request

## Metadata
- Feature slug: `telegram-engagement-notifications`
- Author: Codex
- Created at: 2026-05-07 09:00 UTC
- Priority: high
- Target area: backend-heavy (+ frontend для «поделиться» и deep link)
- Related draft: `.cursor/features/009-telegram-notifications.md` (общая инфраструктура бота/Celery)

## Каноничное описание реализации

**Источник правды после внедрения:** [`docs/features/telegram-engagement-notifications.md`](../../docs/features/telegram-engagement-notifications.md) и [`docs/features/engagement-telegram-notifications.md`](../../docs/features/engagement-telegram-notifications.md).

Кратко:

- **Share:** получатели — только **подписчики** автора карточки (`follower_user_id` при `following_user_id` = автор). Это **не** список «я подписан на них» (`following`).
- **Доставка:** Celery (`tasks.telegram_engagement.*`), см. [`docs/features/celery-redis-workers.md`](../../docs/features/celery-redis-workers.md).
- **Реакции и комментарии:** доменная модель и уведомления реализованы; см. документ engagement выше.

## Problem (исторический контекст)

Нужны исходящие DM бота по продуктовым событиям без блокировки HTTP-ответа API и с предсказуемой валидацией получателей.

## Scope (фактический)

- Share карточки фото+подпись или текстовый шаблон; множественные `recipient_user_ids` в одном запросе.
- Уведомления по реакциям и комментариям — как в `engagement-telegram-notifications.md`.

## Constraints

- Доставка не в синхронном ответе критического API (очередь worker).
- Ошибки Telegram не должны ломать успешное сохранение доменных действий.

## Acceptance Criteria

Актуальные критерии и контракт API — в `docs/features/telegram-engagement-notifications.md`; тесты — `backend/src/tests/api/test_engagement_telegram_notifications.py` и связанные.

## Улучшения после MVP (идеи)

- Группировка «N человек отреагировали», настройки категорий уведомлений, приоритеты очереди — см. исторические пункты ниже при планировании.

### Исторические идеи (не обязательны к сохранению)

- **Группировка**: «Иван и ещё 3 человека отреагировали на ваш комментарий» раз в N минут.
- **Приоритет очереди**: share выше фоновых реакций или наоборот — по продукту.
- **Настройки**: выключить «реакции», оставить «шары»; mute пользователя.
- **Batch** в Redis: счётчик реакций за окно, одно сообщение.
- **Метрики**: delivery rate, причины fail, spam reports.

## Что легко упустить

- Получатель должен был нажать **Start** у бота, иначе личка недоступна.
- Для входящих `/start` и кнопок в будущем может понадобиться webhook — см. корневой `README.md`.
