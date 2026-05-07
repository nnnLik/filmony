# Action log

- **Timestamp:** 2026-05-08T180000Z
- **Feature slug:** feed-ui-card-design
- **Action type:** code + docs
- **Summary:** В раскрываемом блоке комментариев ленты загружаются все комментарии карточки через пагинацию `GET /api/cards/{id}/comments`, список в фиксированной высоте с вертикальным скроллом; добавлен `listAllMovieCardComments` в `cardApi`. Обновлена продуктовая и UI-документация.
- **Files:**
  - `frontend/src/api/cardApi.ts`
  - `frontend/src/components/feed/FeedCard.tsx`
  - `docs/frontend/ui-conventions.md`
  - `docs/features/feed-ui-card-design.md`
  - `docs/features/feed-recommendation-engine.md`
  - `docs/features/movie-card-comments.md`
  - `docs/features/movie-card-comments-telegram-like.md`
  - `docs/features/movie-card-custom-reactions.md`
- **Verification:** `cd frontend && npm run lint && npm run build` (выполнить локально).
