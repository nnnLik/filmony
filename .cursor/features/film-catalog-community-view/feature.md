# Film catalog: community hub on film page

## Scope
- Страница каталога `/films/:filmId` (уже есть в поиске) должна показывать **описание** тайтла из БД и **агрегированные оценки**: кто оценил, балл, контекст просмотра, ссылка на публичную карточку, раскрываемая заметка.
- Бэкенд: пагинируемый список публичных `movie_card` по `film_id`.

## Acceptance criteria
- `GET /api/films/{film_id}/community-cards` с `cursor`/`limit`, 404 если фильма нет, 422 при битом курсоре.
- Сервис `ListFilmCommunityCardsService` с `build`/`execute`, pytest покрывает auth, 404, данные, invalid cursor.
- `FilmDetailPage`: блок «О фильме» (краткое + полное описание), секция «Оценки в Filmony» со списком и «Показать ещё».
- `make backend-test-one target=src/tests/api/test_film_community_routes.py`, `npm run lint && npm run build` в `frontend/`.

## Out of scope (v1)
- Агрегаты средней оценки / гистограммы по фильму (можно позже).
- Скрытие заметок по приватности (сейчас как у публичного списка карточек профиля).
