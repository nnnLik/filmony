# Result: movie-card-create-flow

## Feature
- Slug: `movie-card-create-flow`
- Final status: done

## Implemented
- Добавлены backend сущности и API для фильмов и карточек:
  - `POST /api/films/resolve`
  - `GET /api/films/{film_id}`
  - `POST /api/cards`
- Реализованы backend правила:
  - дубликат `(user_id, film_id)` -> `409`,
  - рейтинг `1..10` с шагом `0.5`,
  - до 5 пользовательских тегов с trim/dedupe.
- Убраны profile stubs:
  - `GET /api/users/{user_id}/cards` отдает реальные карточки,
  - `cards_count` в профиле считает реальные карточки.
- Реализован frontend экран создания карточки `/cards/new` с UI по концепту mock-проекта и стилям Filmony/Telegram UI.

## Changed Files
- `backend/src/models/*` (film/movie_card/movie_card_tag/enums) - доменная модель карточек.
- `backend/src/api/cards/routes.py` - endpoint создания карточки.
- `backend/src/api/films/routes.py` - endpoints resolve/get фильма.
- `backend/src/services/cards/create_movie_card.py` - бизнес-логика создания карточки.
- `backend/src/services/profile/list_user_movie_cards.py` - реальный листинг карточек.
- `backend/src/services/profile/get_user_profile_counts.py` - реальный подсчет карточек.
- `backend/src/tests/api/test_cards_routes.py` - тесты cards/films/profile интеграции.
- `frontend/src/pages/CreateCardPage.tsx` - UI/логика создания карточки.
- `frontend/src/api/cardApi.ts` - клиент cards/films API.
- `frontend/src/pages/FeedPage.tsx` - переход к созданию карточки.
- `frontend/src/pages/ProfilePage.tsx`, `frontend/src/pages/PublicProfilePage.tsx` - отображение реальных карточек.

## Verification
- Команды/checks executed:
  - `ReadLints` для `backend/src` и `frontend/src`.
  - Попытка запуска `make backend-test-one ...` (пропущено средой).
- Results:
  - Lint diagnostics: ошибок не найдено.
  - Полноценный запуск тестов и frontend build требует ручного запуска команд в локальном терминале.

## Automated tests (backend)
- Добавлен модуль: `backend/src/tests/api/test_cards_routes.py`.
- Покрытие:
  - `POST /api/cards`: happy path, `401`, `409`, invalid rating step, too many tags, film not found.
  - profile integration: карточка видна через `GET /api/users/{id}/cards`, `cards_count` обновляется.
  - films flow: resolve + get by id + idempotency + invalid URL.

## Known Limitations
- Проверка командой `make backend-test*` и frontend `npm run lint/build` не выполнена автоматически в этой сессии (shell-команды были пропущены).
- Для `rating` используется `FLOAT`; в сервисе добавлена нормализация к шагу `0.5`, но для долгосрочной строгой математики лучше перейти на scaled integer/decimal.

## Next Steps
- Запустить локально:
  - `make backend-test-one target=src/tests/api/test_cards_routes.py`
  - `make backend-test`
  - `cd frontend && npm run lint && npm run build`

## Iteration update (wizard UX refresh, 2026-05-06)
- `CreateCardPage` переработан в нумерованный flow из 5 шагов:
  1) ссылка на Кинопоиск, 2) подтверждение фильма, 3) оценка и контекст, 4) свои теги, 5) mock sharing + `Готово`.
- На шаге resolve добавлены более понятные пользовательские тексты для ошибок парсинга URL (`empty url`, неверный домен, id не найден).
- На шаге подтверждения показываются постер/название фильма и выбор «Да, далее» / «Нет, другой фильм».
- Шаг оценки оформлен с центральным рейтингом 1..10 (шаг 0.5) и цветными прямоугольными chips для контекстных тегов.
- Финальный шаг оставляет прежнюю бизнес-логику: `POST /api/cards` и переход в `/profile`.

### Additional changed files
- `frontend/src/pages/CreateCardPage.tsx`
- `frontend/src/pages/FeedPage.tsx`

### Additional verification
- `ReadLints` по `frontend/src/pages/CreateCardPage.tsx`, `frontend/src/pages/FeedPage.tsx` — ошибок нет.
