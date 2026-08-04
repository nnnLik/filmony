# Progress: movie-card-favorites

- Миграция `a1b2c3d4e5f6`, модель `MovieCard.is_favorite` / `favorite_marked_at`.
- `UpdateMovieCardService`, схемы и маршруты карт и профиля.
- Лента и деталка отдают `is_favorite`.
- `ListUserMovieCardsService` + `favorites_only`, курсор `fav1.*`.
- `GetUserProfileCountsService` + `favorites_count` в My/Public profile.
- Тесты API в `test_cards_routes.py`, `test_profile_routes.py`.
- Фронтенд по плану — не внедрён в текущем состоянии репозитория.
