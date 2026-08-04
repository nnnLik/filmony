# Plan — engagement-telegram-notifications

## Slices

| ID | Goal |
|----|------|
| S1 | Расширить Bot API клиент (HTML text, стикер), settings, `SendTelegramBotMessageService.parse_mode` |
| S2 | `NotifyTelegramCommentReplyService` + безопасный фоновый вызов из `create_card_comment` |
| S3 | `SetOrToggleUserReactionService` → результат `reaction_was_added` + `NotifyTelegramReactionAddedService` + вызов из `set_user_reaction` |
| S4 | Тесты pytest + `docs/features/engagement-telegram-notifications.md` |

## Agent queue (compact)

1. code-explorer — уже выполнен в сессии (карта: комментарии, реакции, ping Telegram).
2. backend-dev — S1 → S2 → S3 → S4 в одной ветке кода.
3. Зафиксировать progress/result, action-log.
