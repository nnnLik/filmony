# 2026-05-06T05:19:00Z

- Feature slug: `movie-card-comments`
- Action type: code
- Summary: Добавлен индекс ветвления комментариев `(movie_card_id, parent_comment_id, id)` в модели и отдельной Alembic-миграции.
- Files:
  - `backend/src/models/movie_card_comment.py`
  - `backend/src/migrations/versions/c9d2e8a1b7c3_comment_branch_index.py`
- Verification: `ReadLints` по изменённым backend-файлам: ошибок нет.
- Links:
  - `.cursor/active/movie-card-comments/progress.md`
  - `docs/features/movie-card-comments.md`
