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

## Iteration update (poster grid and details page, 2026-05-06)
- Добавлен `GET /api/cards/{card_id}` для получения одной карточки фильма с данными фильма и тегами.
- В профилях (`мой` и `публичный`) карточки переведены в одинаковую сетку постеров фиксированного размера без текстовых подписей.
- Добавлен маршрут и экран деталки карточки `/cards/:cardId` с поддержкой прямого открытия URL.
- На деталке отрисованы реальные данные (постер, название, год, рейтинг, теги) и статические mock-блоки по референсному макету (оценки друзей, лучшая оценка, комментарии, действия).

### Additional changed files
- `backend/src/api/cards/routes.py`
- `backend/src/api/cards/schemas.py`
- `backend/src/services/cards/get_movie_card_details.py`
- `backend/src/tests/api/test_cards_routes.py`
- `frontend/src/components/profile/MoviePosterGrid.tsx`
- `frontend/src/pages/ProfilePage.tsx`
- `frontend/src/pages/PublicProfilePage.tsx`
- `frontend/src/pages/MovieCardDetailPage.tsx`
- `frontend/src/routes.tsx`
- `frontend/src/api/cardApi.ts`

### Additional verification
- `ReadLints` по затронутым backend/frontend файлам — ошибок нет.
- Автотесты через Docker и frontend команды (`npm run lint/build`) требуют ручного запуска: shell-команды в этой сессии пропускаются средой.

## Iteration update (rating redesign and real comments, 2026-05-06)
- На экране детали карточки блок "Твоя оценка" переработан: отображается одно большое число, а цвет и glow вокруг зависят от значения оценки.
- Удален блок "Лучшая оценка".
- Реализована полноценная логика комментариев:
  - backend endpoints `GET /api/cards/{card_id}/comments` и `POST /api/cards/{card_id}/comments`;
  - сохранение комментариев в БД (`movie_card_comment`) с поддержкой `parent_comment_id`;
  - многострочный ввод на фронте с лимитом 250 символов;
  - древовидный рендер ответов без ограничений глубины;
  - отображение автора, аватарки, времени и переход на профиль автора.

### Additional changed files
- `backend/src/models/movie_card_comment.py`
- `backend/src/migrations/versions/d3d7c8a2ef11_add_movie_card_comments.py`
- `backend/src/api/cards/routes.py`
- `backend/src/api/cards/schemas.py`
- `backend/src/services/cards/create_movie_card_comment.py`
- `backend/src/services/cards/list_movie_card_comments.py`
- `backend/src/tests/api/test_cards_routes.py`
- `frontend/src/api/cardApi.ts`
- `frontend/src/api/profileTypes.ts`
- `frontend/src/pages/MovieCardDetailPage.tsx`
- `backend/src/models/__init__.py`
