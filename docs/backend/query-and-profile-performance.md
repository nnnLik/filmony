# Оптимизация запросов к БД и смежные правки бэкенда

Документ фиксирует изменения по итогам работы над производительностью Postgres и упрощением слоя приложения. Миграции выполняет разработчик локально (например `make migrate` после `make start`).

## Миграция `f8e7d6c5b4a3_query_perf_indexes.py`

**Родитель:** `e7f9a8b01234` (user watchlist).

### Новые индексы

| Объект | Индекс | Назначение |
|--------|--------|------------|
| `movie_card` | `ix_movie_card_user_id_created_at_id` на `(user_id, created_at DESC, id DESC)` | Ускорение выборок ленты и потоков по пользователю с сортировкой от новых к старым (см. `ListMovieCardFeedService._ordered_cards`). |
| `movie_card` | `ix_movie_card_created_at_id` на `(created_at DESC, id DESC)` | Поддержка глобальной хронологии без узкого предиката по `user_id` (affinity-скан и похожие сценарии). |
| `user_reaction` | `ix_user_reaction_user_target_kind` на `(user_id, target_kind, target_id)` | Ускорение выборок реакций зрителя и агрегатов по целям (`GetReactionSummariesForTargetsService`: фильтр по `user_id` + область целей). |

### Удалённые индексы (избыточность)

- `ix_user_reaction_user_id` — префикс `user_id` покрывается составным индексом выше и уникальным ограничением `uq_user_reaction_user_target_kind_type` для типичных запросов по пользователю.
- `ix_user_watchlist_film_user_id`, `ix_user_watchlist_film_film_id` — дублируют смысл уже существующего уникального ограничения `uq_user_watchlist_film_user_film` `(user_id, film_id)`; текущие сервисы в основном фильтруют по `user_id` или паре `(user_id, film_id)`.

**Ограничение:** выборки только по `film_id` без `user_id` по watchlist больше не имеют отдельного B-tree по `film_id`. Если появится такой API под нагрузкой — верните точечный индекс под этот запрос.

### Модели SQLAlchemy

Индексы и отказ от `index=True` на отдельных колонках приведены в соответствие с миграцией:

- `models/movie_card.py` — объявлены те же два индекса (в т.ч. `postgresql_ops` для направления).
- `models/user_reaction.py` — добавлен `ix_user_reaction_user_target_kind`, с колонки `user_id` убран отдельный `index=True`.
- `models/user_watchlist_film.py` — убраны `index=True` у `user_id` / `film_id`; остаётся `UniqueConstraint`.

## Один round-trip для счётчиков профиля

**Файл:** `services/profile/get_user_profile_counts.py`

Вместо пяти последовательных `COUNT` выполняется один `SELECT` с четырьмя scalar subquery — те же семантические счётчики, меньше латентности к БД на заголовок профиля.

## Сервис «фильм по id»

**Файлы:** `services/films/get_film_by_id.py`, `services/films/__init__.py`, правка `api/films/routes.py`

Эндпоинт `GET /films/{film_id}` больше не выполняет сырой `select` в роуте: чтение вынесено в `GetFilmByIdService`, в духе тонкого presentation-слоя и толстых сервисов.

## Лента: ограничение размера `seen` в курсоре

**Файлы:** `const/feed.py` (`FEED_CURSOR_SEEN_MAX = 2048`), `services/cards/list_movie_card_feed.py` (`_MergeState.to_payload`)

В JSON курсора записывается не больше **2048** последних (по возрастанию id) значений из множества уже показанных карточек. Это уменьшает размер `next_cursor` при долгой пагинации.

**Продуктовый компромисс:** очень старые id из `seen` из курсора выпадают; теоретически одна и та же карточка может снова попасть в выдачу при крайне длинной сессии листания. На практике окно большое, риск низкий.

## Что намеренно не делалось

**Параллельные `asyncio.gather` для нескольких `session.execute` на одном `AsyncSession` не используются:** в SQLAlchemy 2 async одна сессия не рассчитана на одновременные операции из разных задач. Параллелизм потребовал бы отдельные соединения/сессии или другой пул — это отдельная задача.

## Проверка после миграции

Рекомендуется применить миграцию в окружении с Postgres и прогнать pytest бэкенда (по проектным правилам — в контейнере `filmony-backend`, см. корневой `Makefile`).
