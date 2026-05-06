# Feature: детали статистики профиля (`profile-stats-details`)

## Назначение
Фича добавляет полноценную аналитику карточек фильмов в профиле пользователя и на публичной странице профиля.

## API

### `GET /api/users/{user_id}/stats`
Возвращает агрегированную статистику карточек пользователя:

- `total_movies`
- `average_rating`
- `rating_distribution`
- `year_distribution`
- `popular_tags`
- `watch_with_distribution`
- `mood_after_distribution`
- `top_movies`
- `worst_movies`

### Ошибки
- `401` — без авторизации
- `404` — пользователь не найден

## UI
- `ProfilePage`: вкладка «Статистика» теперь отображает реальные агрегаты.
- `PublicProfilePage`: добавлена вкладка «Статистика», использует тот же компонент `ProfileStatsPanel`.

## Основные файлы
- `backend/src/services/profile/get_user_movie_card_stats.py`
- `backend/src/api/profile/schemas.py`
- `backend/src/api/profile/users_routes.py`
- `backend/src/tests/api/test_profile_routes.py`
- `frontend/src/components/profile/ProfileStatsPanel.tsx`
- `frontend/src/api/profileApi.ts`
- `frontend/src/api/profileTypes.ts`
- `frontend/src/pages/ProfilePage.tsx`
- `frontend/src/pages/PublicProfilePage.tsx`

## Верификация
- По IDE-диагностике (`ReadLints`) ошибок нет.
- Команды `pytest`/`npm` в этой сессии не запускались: shell отклоняется средой (`Rejected: User chose to skip`).
