# 2026-05-06T05:38:00Z

- Feature slug: `movie-card-comments`
- Action type: code
- Summary: Исправлен frontend баг отображения ответов: `MovieCardDetailPage` переведена на поуровневую загрузку `GET comments/replies`, добавлена веточная пагинация и переход в отдельный экран для больших веток.
- Files:
  - `frontend/src/pages/MovieCardDetailPage.tsx`
  - `frontend/src/api/{cardApi.ts,profileTypes.ts}`
- Verification: `ReadLints` по изменённым frontend-файлам: ошибок нет.
- Links:
  - `.cursor/active/movie-card-comments/progress.md`
  - `docs/features/movie-card-comments.md`
