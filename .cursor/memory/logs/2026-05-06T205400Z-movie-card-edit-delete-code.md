# 2026-05-06T20:54:00Z

- Feature slug: `movie-card-edit-delete`
- Action type: code
- Summary: Реализованы backend PATCH/DELETE API и frontend owner menu + edit/delete flows для movie card.
- Files:
  - `backend/src/api/cards/schemas.py`
  - `backend/src/api/cards/routes.py`
  - `backend/src/services/cards/update_movie_card.py`
  - `backend/src/services/cards/delete_movie_card.py`
  - `frontend/src/api/cardApi.ts`
  - `frontend/src/api/profileTypes.ts`
  - `frontend/src/pages/MovieCardDetailPage.tsx`
  - `frontend/src/pages/EditMovieCardPage.tsx`
  - `frontend/src/routes.tsx`
- Verification:
  - `ReadLints` по измененным frontend/backend файлам: ошибок не обнаружено.
