# Progress — profile-stats-details

## Status
- **done**

## Log
- Создан backend сервис `GetUserMovieCardStatsService` для агрегатов по карточкам.
- Добавлен endpoint `GET /api/users/{user_id}/stats` и схемы ответа API.
- Добавлены тесты `test_user_stats_requires_auth`, `test_user_stats_unknown_user_returns_404`, `test_user_stats_aggregates`.
- Во фронтенде добавлены типы/клиент stats и общий компонент `ProfileStatsPanel`.
- `ProfilePage` переведен с заглушки статистики на реальные данные.
- В `PublicProfilePage` добавлена вкладка «Статистика» с тем же компонентом.
