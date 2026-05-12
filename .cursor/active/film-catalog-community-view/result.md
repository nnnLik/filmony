# Result: film-catalog-community-view

## Status
`completed`

## Реализация
- **API:** `GET /api/films/{film_id}/community-cards` — публичные карточки по тайтлу (автор, оценка, компания/настроения, заметка, теги), пагинация keyset по `(updated_at, id)`.
- **Сервис:** `ListFilmCommunityCardsService` (`backend/src/services/films/list_film_community_cards.py`).
- **UI:** `FilmDetailPage` — описание из каталога, секция оценок сообщества, ссылки на профиль и карточку, `<details>` для заметки, догрузка страниц.
- **Клиент:** `getFilmCommunityCardsPage`, типы `FilmCommunityCardItem` и др. в `profileTypes` / `cardApi`.

## Файлы
- `backend/src/services/films/list_film_community_cards.py`
- `backend/src/api/films/routes.py`
- `backend/src/api/films/schemas.py`
- `backend/src/tests/api/test_film_community_routes.py`
- `frontend/src/api/profileTypes.ts`
- `frontend/src/api/cardApi.ts`
- `frontend/src/pages/FilmDetailPage.tsx`

## Проверка
- `make backend-test-one target=src/tests/api/test_film_community_routes.py` — 4 passed.
- `make backend-lint` — OK.
- `cd frontend && npm run lint && npm run build` — OK.

## Ограничения
- Курсор внутри токена не относится к этой фиче.
- Заметки видны всем авторизованным как публичные данные карточки (как в профиле).
