# Feed Recommendation Engine

## Goal

Рекомендательная лента карточек (`GET /api/cards/feed`): смешивание подписок, подписчиков, простого персонального сигнала и discovery с детерминированной пагинацией.

## Каноничность и наследие (007 / 008)

- **Единый документ по ленте** — этот файл и `.cursor/features/feed-recommendation-engine/feature.md`.
- **007** (friends) — исторический контекст: граф задаётся **подписками / подписчиками** (`UserSubscription`).
- **008** (двойники / вектора / Redis) — вне MVP; усилит `personal_affinity` и discovery позже.

## Реализация (backend)

### Источники

| Поток | Описание |
|--------|-----------|
| **own** | Карточки зрителя (`user_id == viewer`), чтобы сохранить UX «вижу свои записи». |
| **subscriptions** | Авторы из подписок: `following_user_id` при `follower_user_id == viewer`. |
| **subscribers** | Авторы-подписчики: `follower_user_id` при `following_user_id == viewer`. |
| **personal_affinity** | Карточки других пользователей без ML: скоринг по пересечению жанров фильма и тегов карточки с профилем зрителя (жанры + теги по его карточкам). |
| **discovery** | Автор **вне** `{viewer} ∪ following ∪ followers}`; свежие карточки вне прямого соцграфа. |

Формула **personal_affinity (MVP)**:

```text
score = GENRE_OVERLAP_WEIGHT * |norm_genres(film) ∩ G_viewer|
      + TAG_OVERLAP_WEIGHT * |norm_tags(card) ∩ T_viewer|
```

- Нормализация: `strip` + `lower()` для сравнения.
- Константы: `backend/src/const/feed.py` (`GENRE_OVERLAP_WEIGHT=2`, `TAG_OVERLAP_WEIGHT=3`).
- Внутри потока сортировка: убывание `score`, затем `created_at`, затем `id`.
- Кандидаты: до `AFFINITY_CANDIDATE_SCAN` последних карточек (`user_id != viewer`), затем отбор и обрезка до `STREAM_POOL_LIMIT`.

### Смешивание и discovery

- Цикл слотов: кортеж `SLOT_PATTERN` в `const/feed.py` (длина 7, один слот — **discovery** на каждые 7 позиций; настраивается через `DISCOVERY_EVERY_N_SLOTS`, сейчас совпадает с длиной паттерна).
- Пустой слот: fallback в порядке `FALLBACK_ORDER`: subscriptions → subscribers → personal_affinity → discovery → own.

### Дедуп и anti-spam

- Глобальный **`seen`** (id карточек) в состоянии курсора — без повторов карточки в цепочке пагинации.
- **Anti-spam**: для **чужих** авторов не брать подряд того же автора или того же `film_id`, если они уже в последних `ANTI_SPAM_WINDOW` выданных позициях (см. `const/feed.py`). Свои карточки зрителя не режутся.

### Cursor (`v1.*`)

- Префикс `v1.` + URL-safe base64(JSON).
- Поля: `v`, `offsets` (следующий индекс в каждом упорядоченном списке потока), `slot_index`, `seen` (все уже выданные id), `tail_authors` / `tail_films` (хвост для anti-spam).
- Повтор запроса с тем же cursor при неизменной БД даёт ту же следующую страницу.
- Старый формат курсора (одно число `movie_card.id`) **не** поддерживается — клиент начинает с первой страницы.

### Производительность

- Запросы: множества подписок; профиль зрителя; до пяти выборок списков `(id, user_id, film_id)` по потокам; батч тегов для affinity; затем одна загрузка `(MovieCard, Film, User)` по `id IN (...)` и существующая гидратация тегов / счётчиков комментариев / превью / реакций (без N+1 на карточку страницы).
- Лимит глубины: каждый поток обрезается `STREAM_POOL_LIMIT`; при долгой прокрутке выдача может закончиться раньше (`next_cursor = null`).

### API

- Контракт ответа не менялся: `MovieCardFeedPageResponse` (`items`, `next_cursor`), тот же набор полей элементов (включая реакции).

## Тесты

- `backend/src/tests/api/test_movie_card_feed_recommendation.py` — happy path, пустой граф, стабильность cursor, discovery при наличии соцграфа, уникальность id на странице.
- `backend/src/tests/api/test_cards_routes.py` — обновлён `test_movie_card_feed_cursor_pagination` под новый cursor.

Прогон: `make backend-test` / `make backend-test-one target=…` в контейнере `filmony-backend`.

## Следующие шаги

- Профили p95 latency, при необходимости кеширование пулов.
- Усиление `personal_affinity` по спеке 008 (соседи по вкусу, вектора, Redis) без дублирования отдельной «ленточной» спеки.
