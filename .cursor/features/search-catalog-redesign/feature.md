# Search Catalog Redesign

## Metadata

| Field | Value |
|-------|-------|
| Feature slug | `search-catalog-redesign` |
| Status | `completed` |
| Stack | frontend + backend |
| Created | 2026-08-10 |
| Updated | 2026-08-10 |

## Problem

Вкладка **Поиск** сейчас ощущается бесполезной:

- Пустое состояние по умолчанию — пользователь видит только подсказки людей, пока не начнёт вводить запрос.
- Смешанная выдача: карточки, темы каталога и пользователи в одном потоке без явного разделения.
- Нет режима **просмотра каталога** — нельзя листать популярные фильмы сообщества без текстового запроса.

## Goal

Переработать вкладку **Поиск** так, чтобы:

1. **По умолчанию** открывался сегмент **«Карточки»** с постраничным каталогом **только фильмов**, отсортированным по популярности в сообществе (`ratings_count`), период **«За всё время»**, без обязательного текстового запроса.
2. Было **явное разделение** «Карточки» vs «Люди» через `SegmentedControl` — без смешивания в одной ленте.
3. В режиме **«Карточки»** доступны сортировки **Популярные** и **Высший средний**, фильтр периода **За всё время | За месяц**, и опциональный `q` как серверный фильтр по названию в том же списке.
4. В режиме **«Люди»** сохраняется текущее поведение: чипы подсказок + поиск пользователей.

## Scope

### In scope (implementation after approval)

- New browse endpoint for films with community metrics, sort, period, optional `q` filter, cursor pagination
- SearchPage redesign: SegmentedControl Карточки|Люди; Cards default = paginated catalog; People = existing suggestions+people search
- Frontend API client + UI for sort + period
- pytest coverage for new/changed backend surface; frontend lint/build for touched files
- `docs/features` after ship

### Out of scope

- Games in catalog
- Mixed cards+topics+people results in Cards mode
- Separate “most ratings” sort (same as Popular)
- Kinopoisk/external provider search redesign
- Materialized popularity counters (unless needed later for perf)
- Collections

## Acceptance criteria

- [x] Default Search opens «Карточки» with paginated films catalog, sort Популярные, period За всё время, no query required
- [x] SegmentedControl «Карточки | Люди»
- [x] Cards mode sorts: Популярные (`ratings_count`), Высший средний (`community_avg_rating`); period: За всё время | За месяц (default всё время); one metric for popularity
- [x] Optional `q` filters same catalog list server-side without switching to mixed search
- [x] Cards mode never shows people/topics mixed sections
- [x] People mode keeps suggestion chips + people search (existing `/api/search` users / suggestions)
- [x] Films only (no games)
- [x] Backend tests for browse endpoint (sort, period, q, pagination, auth if required)
- [x] Feature docs published on closeout

## References

| Area | Path |
|------|------|
| Search page (current UI) | `frontend/src/pages/SearchPage.tsx` |
| Search API client | `frontend/src/api/searchApi.ts` |
| Catalog search tab docs | `docs/features/catalog-search-tab.md` |
| SegmentedControl component | `frontend/src/components/ui/SegmentedControl.tsx` |
| Profile tabs pattern | `frontend/src/components/profile/ProfileMainTabs.tsx` |
| Feed page tabs pattern | `frontend/src/pages/FeedPage.tsx` |
| Genre film list response shape | `backend/src/api/genres/schemas.py` — `GenreFilmItemResponse` |
| Genre films route (cursor pagination pattern) | `backend/src/api/genres/routes.py` |
| Genre/director film lists with community metrics | `backend/src/services/genres/list_genre_rated_films.py`, `backend/src/services/directors/list_director_rated_films.py` |
| Community stats aggregation | `backend/src/services/catalog/get_catalog_community_stats.py`, `backend/src/services/catalog/batch_catalog_community_stats.py` |

### `GenreFilmItemResponse` fields (target item shape)

| Field | Type | Notes |
|-------|------|-------|
| `film_id` | `int` | Film identifier |
| `title` | `str` | Display title |
| `year` | `int \| null` | Release year |
| `poster_url` | `str \| null` | Poster image URL |
| `genres` | `list[str]` | Genre labels |
| `community_avg_rating` | `float \| null` | Mean of rated user cards |
| `ratings_count` | `int` | Count of rated user cards |
| `my_card_id` | `int \| null` | Current user's card id if rated (optional but useful) |

## Locked decisions

1. **Каталог только фильмов** — игры и прочие типы каталога не входят в browse-лист Search.
2. **SegmentedControl «Карточки | Люди»** — default «Карточки»; в Cards mode никогда не показывать людей/темы вперемешку.
3. **Две сортировки в Cards mode:** «Популярные» (`ratings_count` DESC) и «Высший средний» (`community_avg_rating` DESC). Отдельной сортировки «Больше всего оценок» нет — она совпадает с «Популярные».
4. **Фильтр периода:** «За всё время» (default) | «За месяц» (последние 30 дней активности `UserCard.created_at`); применяется к обоим метрикам (count и avg).
5. **Один browse-endpoint с `q` как фильтром** — пустой `q` = browse; `q` ≥ 2 символов фильтрует тот же список server-side (sort+period сохраняются); Cards mode не вызывает mixed `/api/search` для списка фильмов.
