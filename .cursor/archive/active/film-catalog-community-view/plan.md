# Plan: film-catalog-community-view

1. Сервис списка карточек по `film_id` + keyset cursor.
2. Схемы Pydantic и маршрут `GET /films/{id}/community-cards` перед `GET /films/{id}`.
3. Pytest `test_film_community_routes.py`.
4. Типы и `getFilmCommunityCardsPage` во фронте; доработка `FilmDetailPage`.
5. Документация и action log.
