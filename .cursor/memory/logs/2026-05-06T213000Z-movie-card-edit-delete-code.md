# 2026-05-06T21:30:00Z

- Feature slug: `movie-card-edit-delete`
- Action type: code
- Summary: Исправлена навигация после редактирования карточки: вместо push на detail используется history back, чтобы «Назад» не возвращала на экран редактирования.
- Files:
  - `frontend/src/pages/EditMovieCardPage.tsx`
- Verification:
  - `ReadLints` для изменённого файла: без ошибок.
