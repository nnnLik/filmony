# 2026-05-06T05:18:00Z

- Feature slug: `movie-card-comments`
- Action type: code
- Summary: Реализованы backend сервисы и API для комментариев/ответов под карточкой с публичным чтением, auth-only созданием, валидацией текста, проверкой принадлежности parent и cursor пагинацией.
- Files:
  - `backend/src/services/cards/create_movie_card_comment.py`
  - `backend/src/services/cards/list_movie_card_comments.py`
  - `backend/src/services/cards/__init__.py`
  - `backend/src/api/cards/{schemas.py,routes.py}`
  - `backend/src/tests/api/test_cards_routes.py`
- Verification: `ReadLints` по изменённым backend-файлам: ошибок нет.
- Links:
  - `.cursor/active/movie-card-comments/progress.md`
  - `docs/features/movie-card-comments.md`
