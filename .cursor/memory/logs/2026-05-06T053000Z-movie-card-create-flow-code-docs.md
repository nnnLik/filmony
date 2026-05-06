# 2026-05-06T05:30:00Z

- Feature slug: `movie-card-create-flow`
- Action type: code | docs
- Summary: Переработан UI оценки на деталке, удален блок "Лучшая оценка", внедрена система комментариев с БД, древовидными ответами, многострочным вводом (<=250), отображением автора/аватарки/времени и переходом на профиль автора.
- Files:
  - `backend/src/models/movie_card_comment.py`
  - `backend/src/migrations/versions/d3d7c8a2ef11_add_movie_card_comments.py`
  - `backend/src/api/cards/{routes.py,schemas.py}`
  - `backend/src/services/cards/{create_movie_card_comment.py,list_movie_card_comments.py}`
  - `backend/src/tests/api/test_cards_routes.py`
  - `backend/src/models/__init__.py`
  - `frontend/src/api/{cardApi.ts,profileTypes.ts}`
  - `frontend/src/pages/MovieCardDetailPage.tsx`
  - `.cursor/active/movie-card-create-flow/{progress.md,result.md}`
  - `docs/features/movie-card-create-flow.md`
- Verification: `ReadLints` по измененным backend/frontend файлам — ошибок нет.
- Links:
  - `.cursor/active/movie-card-create-flow/progress.md`
  - `docs/features/movie-card-create-flow.md`
