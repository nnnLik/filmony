# 2026-05-06T20:35:00Z

- Feature slug: `movie-card-comments-telegram-like`
- Action type: code
- Summary: Переведен backend list comments на плоскую выдачу, переписан frontend комментариев на Telegram-like reply-preview, удален thread-screen из роутинга и кода.
- Files:
  - `backend/src/services/cards/list_movie_card_comments.py`
  - `backend/src/api/cards/routes.py`
  - `backend/src/tests/api/test_cards_routes.py`
  - `frontend/src/pages/MovieCardDetailPage.tsx`
  - `frontend/src/routes.tsx`
  - `frontend/src/pages/MovieCardCommentThreadPage.tsx`
- Verification:
  - `ReadLints` по измененным backend/frontend файлам: ошибок не найдено.
