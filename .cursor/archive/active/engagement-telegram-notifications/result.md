# result — engagement-telegram-notifications

## Реализовано

- `NotifyTelegramCommentReplyService` + вызов из `POST /api/cards/{id}/comments` при наличии `parent_comment_id`.
- `NotifyTelegramReactionAddedService` + вызов из `POST /api/reactions` только если реакция **добавлена** (`SetUserReactionOutcome`).
- Расширены Bot API клиент (`parse_mode`), `SendTelegramBotMessageService`.
- Общая доставка `deliver_engagement_html_message` с подавлением ошибок чата.

## Файлы

См. `docs/features/engagement-telegram-notifications.md` и `progress.md`.

## Проверка

По правилам репозитория: pytest и ruff в Docker — см. корневой `Makefile` (пользователь может выполнить локально).
