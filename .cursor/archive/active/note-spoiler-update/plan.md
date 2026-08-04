# Plan: note-spoiler-update

1. Константа `WATCH_NOTE_MAX_LEN = 1000`, миграция `user_card.watch_note`, обновление schemas/services/models.
2. Модуль `spoiler_tokens` + валидация в comments/posts/watch notes.
3. Frontend: `spoilerTokens.ts`, `SpoilerRevealBlock`, `CommentSpoilerToggleButton`, рендер в `CommentBodyWithReactionTokens`.
4. Composer UI: Create/Edit card, FeedCard, FeedPostCard, FeedComposeSheet, FeedPostDetail, MovieCardDetail.
5. Тесты и docs.
