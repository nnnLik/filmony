# 2026-05-06T05:32:00Z

- Feature slug: `movie-card-comments`
- Action type: code
- Summary: Контракт комментариев расширен полем `total_descendants_count`; backend листинг считает суммарных потомков через recursive CTE, роуты/схемы и тесты обновлены.
- Files:
  - `backend/src/services/cards/list_movie_card_comments.py`
  - `backend/src/api/cards/{schemas.py,routes.py}`
  - `backend/src/tests/api/test_cards_routes.py`
- Verification: `ReadLints` по изменённым backend-файлам: ошибок нет.
- Links:
  - `.cursor/active/movie-card-comments/progress.md`
  - `docs/features/movie-card-comments.md`
