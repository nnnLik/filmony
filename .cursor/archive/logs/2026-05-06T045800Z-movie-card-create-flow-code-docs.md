# 2026-05-06T04:58:00Z

- Feature slug: `movie-card-create-flow`
- Action type: code | docs
- Summary: Лента упрощена; экран создания карточки переработан в нумерованный wizard из 5 шагов с confirm-этапом после resolve URL, ошибками парсинга Кинопоиска, этапами рейтинга/тегов и финальным созданием карточки.
- Files:
  - `frontend/src/pages/CreateCardPage.tsx`
  - `frontend/src/pages/FeedPage.tsx`
  - `.cursor/active/movie-card-create-flow/{plan.md,progress.md,result.md}`
  - `docs/features/movie-card-create-flow.md`
- Verification: `ReadLints` по `frontend/src/pages/CreateCardPage.tsx`, `frontend/src/pages/FeedPage.tsx` — ошибок нет.
- Links:
  - `.cursor/active/movie-card-create-flow/progress.md`
  - `docs/features/movie-card-create-flow.md`
