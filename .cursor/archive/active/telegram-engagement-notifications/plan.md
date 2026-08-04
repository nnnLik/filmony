# Implementation Plan

## Feature
- Slug: `telegram-engagement-notifications`
- Source spec: `.cursor/features/telegram-engagement-notifications/feature.md`

## Goal
- Дать пользователю возможность **отправить карточку** выбранному **подписчику** (following) через уведомление в Telegram-боте и заложить события для **реакций** на карточку/комментарий.

## Step-by-Step Plan
1. Зафиксировать хранение `telegram_user_id` / идентификатора для Bot API `sendMessage` (аудит модели `User`).
2. Реализовать тонкий клиент Telegram Bot API (отправка текста + ссылка), конфиг из `settings`.
3. Ввести слой доставки: очередь (Celery при наличии) + retry с backoff на `429`/сетевые ошибки.
4. Реализовать `ShareMovieCardToFollowedUserService` (или аналог): проверка подписки, dedupe, постановка задачи отправки.
5. Добавить `POST /api/cards/{card_id}/share` + схемы + тесты (`401`, не подписка, happy path, idempotent repeat).
6. Логирование/outbox: статус `pending/sent/failed`, причина `blocked_bot` / `chat_not_found`.
7. (Когда появятся реакции) хук на создание реакции → `NotifyReactionService` с теми же лимитами.
8. Frontend: UI выбора получателя из подписок + вызов API; при ошибке «получатель не запускал бота» — понятный текст.
9. Deep link: согласовать формат `startapp` / query с `frontend` и обновить роутинг при необходимости.
10. Обновить `docs/features/telegram-engagement-notifications.md`, `result.md`, action-log.

## Files Expected To Change
- `backend/src/conf/settings.py` (при необходимости уточнить telegram-настройки)
- `backend/src/integrations/telegram/*` (новый клиент)
- `backend/src/services/cards/*` или `backend/src/services/notifications/*`
- `backend/src/api/cards/routes.py` или отдельный `notifications` router
- `backend/src/workers/*` (если есть Celery)
- `backend/src/tests/api/*`, `backend/src/tests/services/*`
- `frontend/src/api/*`, страница карточки / создания карточки
- `docs/features/telegram-engagement-notifications.md`

## Verification Plan
- `make backend-test-one target=...` для новых тестов share и сервиса доставки (Docker).
- Ручной smoke в dev: два тестовых пользователя, оба нажали /start у бота; share → сообщение получено.
- Проверка dedupe: двойной запрос не шлёт второе сообщение в окне TTL.
