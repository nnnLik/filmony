# Social Depth Pack

Четыре связанные социальные фичи для усиления «Позже», совместных просмотров и вовлечения.

## A — Пересечение «Позже»

**API:** `GET /api/me/watchlist/overlaps?limit=20` (max 50)

Возвращает тайтлы из watchlist текущего пользователя, которые также есть в «Позже» у **взаимных** подписчиков (`mutual subscriptions`).

**UI:**
- Секция «Ещё хотят посмотреть» на вкладке «Позже» профиля
- Баннер «Ещё у N в «Позже»» на странице фильма/карточки
- CTA «Смотрим вместе» → `/watchlist/new` с prefill `watchWithUserIds` + confirm sheet

**Backend:** [`ListWatchlistOverlapsService`](../../backend/src/services/watchlist/list_watchlist_overlaps.py)

## B — Совместный просмотр → пост

**Модель:** `watch_session` — координация группы после watch-with инвайта.

**Жизненный цикл:**
1. Создание watchlist с `watch_with_user_ids` → session `planned`
2. Участник апгрейдит planned→rated → прогресс session
3. Когда все оценили **или** 48ч после первой оценки (≥2 оценки) → feed post инициатора + Telegram nudge

**Feed post:** `watch_session_id` на `feed_post`; в ленте — `co_view_splits: [{user_id, slug, rating}]`.

**Celery:** `tasks.watch_session.finalize_watch_session_if_ready` (worker; beat не в compose).

## C — Спорная карточка недели

**Круг:** following (как «Друзья оценили»).

**Метрика:** `max(rating) − min(rating)` при ≥3 оценках; окно 7 дней с fallback.

**API:** `GET /api/me/weekly-controversy`

**Доставка:** Celery `send_weekly_controversy_digests` (расписание в деплое) + чип на community page: «Разброс X · N друзей».

## D — Стрик оценок

**Правило:** календарный день UTC с ≥1 rated card (`completed_at`, не planned).

**API:** `POST /api/streaks/batch` — только пользователи с `current ≥ 4`; `GET /api/me/streak` — свой полный счётчик.

**UI:** пылающая цифра рядом с ником (градиент + glow, интенсивность 4→10); без лидерборда.

**Компоненты:** `RatingStreakBadge`, `useRatingStreaksOfUsers`.

## Миграции

- `d5e6f7a89012` — `watch_session`, `feed_post.watch_session_id`
- `d5e6f7a8b901` — `weekly_controversy_state`

## Тесты

- `backend/src/tests/api/test_watchlist_overlaps_routes.py`
- `backend/src/tests/services/test_watch_session_services.py`
- `backend/src/tests/api/test_weekly_controversy_routes.py`
- `backend/src/tests/api/test_streaks_routes.py`

Полный прогон: `make backend-test` (535 passed). Frontend: `npm run lint && npm run build`.
