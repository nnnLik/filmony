# Result: profile-later-tab-back-nav

## Status
`completed`

## Что сделано
- Сегмент фильмов профиля («Оценённые» / «Позже») сохраняется в query-параметре `?movies=watchlist`.
- `ProfilePage` читает и записывает сегмент через `useProfileMoviesSegmentFromUrl`.
- Навигация из `WatchlistForm` и `TelegramMiniAppStartParamRedirect` передаёт `movies=watchlist`, чтобы возврат назад попадал на вкладку «Позже».

## Изменённые файлы
- `frontend/src/lib/profileMoviesSegment.ts`
- `frontend/src/hooks/useProfileMoviesSegmentFromUrl.ts`
- `frontend/src/pages/ProfilePage.tsx`
- `frontend/src/components/create/WatchlistForm.tsx`
- `frontend/src/navigation/TelegramMiniAppStartParamRedirect.tsx`
- `frontend/src/lib/__tests__/profileMoviesSegment.test.ts`
- `frontend/src/hooks/__tests__/useProfileMoviesSegmentFromUrl.test.tsx`

## Проверка
- `cd frontend && npm test -- profileMoviesSegment useProfileMoviesSegmentFromUrl` — 6 passed
- `cd frontend && npm run lint` — passed
