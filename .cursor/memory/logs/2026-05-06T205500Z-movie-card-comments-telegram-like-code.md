# 2026-05-06T20:55:00Z

- Feature slug: `movie-card-comments-telegram-like`
- Action type: code | docs
- Summary: Поменян порядок комментариев на oldest-first, адаптирована cursor-пагинация и обновлен тест плоской выдачи с документацией фичи.
- Files:
  - `backend/src/services/cards/list_movie_card_comments.py`
  - `backend/src/tests/api/test_cards_routes.py`
  - `docs/features/movie-card-comments-telegram-like.md`
  - `.cursor/active/movie-card-comments-telegram-like/progress.md`
- Verification:
  - `ReadLints` по измененным файлам: ошибок нет.
