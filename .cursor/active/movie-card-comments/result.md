# Result: movie-card-comments

## Feature
- Slug: `movie-card-comments`
- Final status: done

## Implemented
- Добавлены backend правила комментариев под карточкой фильма с неограниченной вложенностью ответов:
  - `POST /api/cards/{card_id}/comments` — создание комментария или ответа (по `parent_comment_id`), только для авторизованных пользователей.
  - `GET /api/cards/{card_id}/comments` — публичный список корневых комментариев (cursor pagination).
  - `GET /api/cards/{card_id}/comments/{comment_id}/replies` — публичный список ответов конкретного комментария (cursor pagination).
- Реализована валидация комментария в сервисе:
  - `trim`, запрет пустого текста, ограничение длины (250),
  - проверка существования карточки,
  - проверка существования `parent_comment_id`,
  - проверка, что parent принадлежит той же карточке.
- В API-ответы добавлены:
  - `replies_count` для каждого комментария,
  - `next_cursor` для пагинации.
- Добавлен индекс для ветвления комментариев:
  - `(movie_card_id, parent_comment_id, id)`.

## Changed Files
- `.cursor/features/movie-card-comments/feature.md`
- `.cursor/active/movie-card-comments/plan.md`
- `.cursor/active/movie-card-comments/progress.md`
- `.cursor/active/movie-card-comments/result.md`
- `docs/features/movie-card-comments.md`
- `backend/src/models/movie_card_comment.py`
- `backend/src/migrations/versions/c9d2e8a1b7c3_comment_branch_index.py`
- `backend/src/services/cards/create_movie_card_comment.py`
- `backend/src/services/cards/list_movie_card_comments.py`
- `backend/src/services/cards/__init__.py`
- `backend/src/api/cards/schemas.py`
- `backend/src/api/cards/routes.py`
- `backend/src/tests/api/test_cards_routes.py`
- `.cursor/memory/logs/action-log-from-2026-05-06T103000Z.md`

## Verification
- `ReadLints` по изменённым backend-файлам — ошибок не найдено.
- Попытка запуска backend-команд через shell (`make backend-test*`) в этой сессии была отклонена средой (`Rejected: User chose to skip`).

## Known Limitations
- В этой сессии нет подтверждённого прогона `pytest` внутри Docker из-за ограничения shell.

## Next Steps
- Запустить локально:
  - `make backend-test-one target=src/tests/api/test_cards_routes.py`
  - `make backend-test`
