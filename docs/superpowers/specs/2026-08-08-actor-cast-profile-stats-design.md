# Actor cast enrichment + profile stats + actor detail page — Design Spec

**Date:** 2026-08-08  
**Status:** draft — ready for review  
**Feature slug:** `actor-cast-profile-stats`

---

## 1. Context

Сегодня Filmony хранит **режиссёра** на уровне `Film` (`primary_director_kinopoisk_id`, имя, постер) и строит вокруг этого статистику профиля, страницу `/directors/:kinopoiskId` и фильтр карточек по режиссёру. **Актёры** в продукте отсутствуют: нет таблиц, нет обогащения из Kinopoisk, нет распределения в stats и нет детальной страницы.

Kinopoisk Unofficial API уже используется для staff (`GET /v1/staff?filmId=` через `KinopoiskProviderTransport.get_staff_by_film_id`) — сейчас из ответа берётся только первый `professionKey=DIRECTOR`. Тот же эндпоинт содержит актёрский состав с `professionKey=ACTOR`, порядком биллинга и полем `description` (роль персонажа).

Пользователи оценивают фильмы (`UserCard` с `is_planned=False`); cast нужен **только для таких фильмов**, потому что stats и taste-диаграммы считаются по оценённым карточкам (как для режиссёров). Обогащение **на уровне фильма** (общее для всех пользователей): один запрос KP на фильм, idempotent, не привязано к конкретному user.

---

## 2. Goals

1. **Данные** — таблицы `person` и `film_actor`; топ-10 актёров (`professionKey=ACTOR`) в порядке ответа KP для каждого фильма с хотя бы одной оценённой карточкой.
2. **Обогащение** — сервис `EnsureFilmCastService` (build/execute), вызов из `CreateUserCardService` при создании оценки и при апгрейде planned→rated; management-команда backfill для исторических фильмов.
3. **Stats** — расширить `GET /api/users/{id}/stats`: `actor_distribution`, `insights.top_actor_*`, `unique_actors_count`; только non-planned карточки (`is_planned=False`, `rating >= 1`).
4. **API актёра** — `GET /api/actors/{kinopoisk_id}` и `GET /api/actors/{kinopoisk_id}/films` с `films_count` и списком фильмов **владельца профиля** (оценённые им фильмы с этим актёром), не глобальный каталог.
5. **Фильтр карточек** — query `actor_kinopoisk_id` на списке оценённых карточек профиля (аналог `director_kinopoisk_id`).
6. **Frontend** — insights и taste-donut для актёров в `ProfileStatsPanel`, `ActorDetailPage` (`/actors/:kinopoiskId`), drill-down из stats, фильтр в rated cards.

---

## 3. Non-goals (v1)

| Исключено | Примечание |
|-----------|------------|
| Актёры на карточке/деталке фильма | Только stats + actor detail |
| Cast для watchlist / planned-only | `is_planned=True` не триггерит KP |
| Обогащение всего каталога без оценок | Только фильмы с ≥1 rated `UserCard` |
| `top_actor` в monthly recap | Отложено |
| TMDB actors / credits | Только Kinopoisk staff |
| Глобальный browse `GET /api/actors` (каталог) | Опционально после v1; маршрут `/actors` index не в v1 |
| Синхронизация полного cast KP (все актёры фильма) | Только top-10 ACTOR |
| Пересчёт cast при смене состава на KP | Данные immutable после первого успешного fetch |

---

## 4. Data model

### 4.1 `person`

Нормализованная сущность актёра (и в перспективе других персон KP; v1 — только актёры из cast).

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `INTEGER` PK | serial |
| `kinopoisk_id` | `INTEGER` | `UNIQUE NOT NULL` — `staffId` из KP |
| `name` | `VARCHAR` | `NOT NULL` — `nameRu` → fallback `nameEn` |
| `poster_url` | `VARCHAR` | nullable |
| `created_at` | `TIMESTAMPTZ` | default now |
| `updated_at` | `TIMESTAMPTZ` | on update |

**Indexes:** `uq_person_kinopoisk_id` (unique), при необходимости `ix_person_name` для будущего browse.

### 4.2 `film_actor`

Связь фильм ↔ актёр с порядком биллинга и ролью.

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | `INTEGER` PK | serial |
| `film_id` | `INTEGER` FK → `film.id` | `NOT NULL`, `ON DELETE CASCADE` |
| `person_id` | `INTEGER` FK → `person.id` | `NOT NULL`, `ON DELETE CASCADE` |
| `billing_order` | `SMALLINT` | `NOT NULL`, check `1 <= billing_order <= 10` |
| `role` | `VARCHAR` | nullable — из KP `description` |
| `created_at` | `TIMESTAMPTZ` | default now |

**Constraints:**

- `UNIQUE (film_id, person_id)`
- `UNIQUE (film_id, billing_order)`

**Indexes:**

- `ix_film_actor_film_id` — выборка cast по фильму
- `ix_film_actor_person_id` — агрегация stats и фильтр карточек по актёру

### 4.3 Расширение Kinopoisk DTO

`KinopoiskStaffMemberDTO` дополняется полем `description: str | None` (KP JSON key `description`) для сохранения роли в `film_actor.role`.

### 4.4 Парсинг top-10 ACTOR

Алгоритм (чистая функция, unit-testable):

1. Взять tuple staff из `get_staff_by_film_id(kinopoisk_id)`.
2. Отфильтровать `profession_key == 'ACTOR'` (case-sensitive, как в KP).
3. Сохранить **порядок ответа API** (не сортировать по имени).
4. Взять первые 10; для каждого: `billing_order` = 1-based index в этом срезе.
5. `role` = trimmed `description` или `NULL` если пусто.
6. `name` = `display_name()` из DTO (`nameRu` → `nameEn`); `poster_url` = `poster_url` из KP staff.

Эпизодические роли в top-10 KP допустимы в v1 (не дедуплицируем по имени персонажа).

---

## 5. Enrichment flow

### 5.1 `EnsureFilmCastService`

**Расположение:** `backend/src/services/cast/ensure_film_cast.py`, `backend/src/services/cast/parse_top_actors.py`.

**Контракт:**

```python
@dataclass
class EnsureFilmCastService:
    _session: AsyncSession
    _kp_transport: KinopoiskProviderTransport

    @classmethod
    def build(cls, session: AsyncSession) -> Self: ...

    async def execute(self, film_id: int) -> None:
        """Idempotent: ensure film_actor rows for rated film; no-op if already present."""
```

**Логика `execute`:**

1. Загрузить `Film` по `film_id`; если нет `kinopoisk_id` — return (no-op).
2. Проверить существование любой строки `film_actor` для `film_id` — если есть, **return** (idempotent skip, без KP).
3. `staff = await _kp_transport.get_staff_by_film_id(film.kinopoisk_id)`.
4. `actors = parse_top_actors(staff)` (§4.4).
5. Для каждого актёра: `upsert person` по `kinopoisk_id` (`name`, `poster_url` из §4.4; при conflict обновить непустые поля); `insert film_actor` (в одной транзакции).
6. При пустом списке ACTOR — commit без строк `film_actor` (фильм без cast).

**Idempotency и пустой cast (v1):** skip KP только если для `film_id` уже есть ≥1 строка `film_actor`. **Negative cache не в v1:** после успешного KP-ответа с 0 ACTOR строк не создаётся; следующий вызов снова идёт в KP. Повторные KP для одного фильма возможны, если разные пользователи первыми оценят фильм без актёров в staff — **принятый риск v1** (редко). Backfill выбирает только фильмы без любых `film_actor` строк (§5.3), поэтому не ретраит уже обработанные фильмы с пустым cast.

**Ошибки KP:** логировать warning/error; **не пробрасывать** в `CreateUserCardService` — создание карточки успешно. Backfill логирует и переходит к следующему фильму.

### 5.2 Триггеры (только rated)

| # | Событие | Где | Условие |
|---|---------|-----|---------|
| 1 | Создание оценённой карточки | `CreateUserCardService.execute` после commit | `is_meaningful_rated_card(card)` (`is_planned=False`, `rating >= 1`, `film_id NOT NULL`) |
| 2 | Апгрейд planned → rated | `CreateUserCardService._finalize_upgraded_planned` после commit | то же: `is_meaningful_rated_card(entity)` |
| 3 | Management backfill | `manage_backfill_film_cast.py` | distinct `film_id` из `UserCard` с `_rated_card_filters()` и без строк `film_actor` |

**Не триггерить:** создание planned card; правка рейтинга; удаление карточки (cast на фильме остаётся).

**Вызов:** после commit карточки — `await EnsureFilmCastService.build(session).execute(film_id)` в том же request/task; KP-ошибки глотать внутри `EnsureFilmCastService` (не fail card create).

### 5.3 Management backfill

**Файл:** `backend/src/manage_backfill_film_cast.py`

**Выборка фильмов:**

```sql
SELECT DISTINCT uc.film_id
FROM user_card uc
WHERE uc.is_planned = FALSE
  AND uc.rating >= 1
  AND uc.film_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM film_actor fa WHERE fa.film_id = uc.film_id)
ORDER BY uc.film_id
```

**Опции CLI:** `--dry-run`, `--limit N`, `--sleep SEC` (default 0.15), `--batch-size` (default 50).

**429 / rate limit:** при HTTP 429 — exponential backoff (например 2s → 4s → 8s, max 60s), затем retry того же фильма; счётчик ошибок в summary в конце прогона.

**Запуск (Docker-first):**

```bash
docker compose exec -w /opt/app backend \
  python src/manage_backfill_film_cast.py [--dry-run] [--limit N]
```

---

## 6. API

### 6.1 Stats — `GET /api/users/{user_id}/stats`

Расширение существующего ответа (схемы в `api/profile/schemas.py`, логика в `GetUserCardStatsService` / `get_user_card_stats.py`).

**Новые поля:**

```json
{
  "actor_distribution": [
    {
      "kinopoisk_id": 733,
      "name": "Леонардо ДиКаприо",
      "poster_url": "https://…",
      "count": 12
    }
  ],
  "insights": {
    "top_actor_kinopoisk_id": 733,
    "top_actor_name": "Леонардо ДиКаприо",
    "top_actor_count": 12,
    "unique_actors_count": 847
  }
}
```

**Правила агрегации:**

- Учитываются только карточки с `_rated_card_filters()` (`services/directors/get_director_summary.py`): `is_planned=False`, `rating >= 1`, `film_id NOT NULL`. **Out of scope v1:** менять существующие `director_distribution` / genre stats в том же endpoint (сейчас часть stats считает только `is_planned=False` без `rating >= 1`).
- Для каждой оценённой карточки фильм даёт **вклад каждому** актёру из `film_actor` (до 10 на фильм); один фильм с 3 актёрами из top-10 увеличивает count трёх актёров.
- `actor_distribution` сортировка: `count DESC`, tie-break `name ASC`, `kinopoisk_id ASC`.
- `top_actor_*` — первый элемент distribution (или null/0 если пусто).
- `unique_actors_count` — число distinct `person.kinopoisk_id` в distribution.
- Planned / watchlist-only карточки **не входят**.

**SQL-скетч:** join `user_card` → `film_actor` → `person`, `GROUP BY person.kinopoisk_id`, фильтр по `user_id` и rated filters.

### 6.2 Actor summary — `GET /api/actors/{kinopoisk_id}`

**Router:** `api/actors/routes.py`, prefix `/actors`, tag `actors`.

**Query:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `user_id` | UUID | текущий пользователь | Чьи оценённые фильмы считать; для public profile drill-down передаётся id владельца профиля |

**Response `ActorSummaryResponse`:**

| Field | Type | Description |
|-------|------|-------------|
| `kinopoisk_id` | int | KP staff id |
| `name` | string | из `person.name` |
| `poster_url` | string \| null | из `person.poster_url` |
| `films_count` | int | distinct rated films **указанного `user_id`** с этим актёром |

**404:** нет `person` с таким `kinopoisk_id` **или** `films_count == 0` для запрошенного `user_id` (согласовано с UX «пустой актёр не показываем»).

**Авторизация:** запрос своих данных — всегда; чужой `user_id` — только если профиль/stats этого пользователя уже публично доступны (та же политика, что для `GET /api/users/{id}/stats`).

**Отличие от directors:** `GetDirectorSummaryService` считает community-wide rated films; actor summary **user-scoped**.

### 6.3 Actor films — `GET /api/actors/{kinopoisk_id}/films`

**Query:** `user_id` (как выше), `cursor`, `limit` (default 20, max 50).

**Response item `ActorFilmItemResponse`:**

| Field | Type | Description |
|-------|------|-------------|
| `film_id` | int | |
| `title` | string | |
| `year` | int \| null | |
| `poster_url` | string \| null | |
| `genres` | string[] | |
| `role` | string \| null | роль актёра в этом фильме (`film_actor.role`) |
| `my_card_id` | int \| null | id карточки **viewer** если viewer оценил тот же фильм (как у directors) |
| `rating` | float \| null | оценка **владельца `user_id`** для этого фильма |
| `rated_at` | datetime \| null | `completed_at` карточки владельца |

**Сортировка:** `rated_at DESC`, tie-break `film_id DESC` (персональная хронология оценок владельца профиля).

**Пагинация:** cursor `rated_at_iso:film_id` — по образцу directors (`ratings_count:film_id`), адаптировано под user-scoped список.

**Сервисы:**

- `GetActorSummaryService`
- `ListActorRatedFilmsService`

Оба используют join `user_card` (owner) + `film_actor` + `person` + `film`, фильтр `person.kinopoisk_id = :kinopoisk_id` и rated filters на карточке владельца.

### 6.4 Cards filter — `GET /api/users/{user_id}/cards` (rated)

Новый query param:

```
actor_kinopoisk_id: int | None
```

Фильтр: оставить только карточки, где `film_id` связан с `film_actor.person.kinopoisk_id = actor_kinopoisk_id`. Комбинируется с существующим `director_kinopoisk_id` (AND если оба заданы).

---

## 7. Frontend

### 7.1 API client

**Файл:** `frontend/src/api/actorsApi.ts` — типы (`ActorSummaryResponse`, `ActorFilmItemResponse`, …) и клиенты `getActorSummary`, `getActorFilmsPage` (опциональный `userId` для public profile).

### 7.2 Profile stats

**`ProfileStatsPanel`:**

- Новый taste-tab или секция **«Актёры»** — donut chart по `actor_distribution` (тот же компонент/паттерн, что genre/director/franchise).
- Insights row: **«Топ актёр»** — `insights.top_actor_name` + count, ссылка на `/actors/{top_actor_kinopoisk_id}?userId=…` при drill-down с чужого профиля.
- Legend collapse top-8 + «Ещё N» (существующий UX § profile-streak-stats-legend).

**Public profile:** при рендере stats передавать `profileUserId` в ссылки и API.

### 7.3 `ActorDetailPage`

**Маршрут:** `/actors/:kinopoiskId` в `routes.tsx` (lazy load).

**Поведение:** зеркало `DirectorDetailPage`, но:

- Заголовок «Актёр»
- Summary: имя, постер, `films_count` (оценённые фильмы **владельца контекста**)
- Список фильмов с колонкой/подписью **роль** (`role`)
- Query `userId` из search params для public profile context; default — текущий пользователь

**Компоненты:** переиспользовать `CatalogPageShell`, `CatalogEntitySummaryCard`, `CatalogFilmsSection`; при необходимости `ActorChip` (аналог `DirectorChip`) для будущего — в v1 достаточно ссылок из stats.

### 7.4 Rated cards filter

**`ProfileRatedCardsFilters`:** dropdown/пикер актёров (по аналогии с режиссёрами) — источник: top N из `actor_distribution` stats snapshot или отдельный lightweight endpoint **не в v1**; v1 — список из уже загруженного stats при активной вкладке statistics cache / повторный fetch stats keys.

Установка query `actor_kinopoisk_id` в URL карточек профиля; chip «актёр: …» в active filters.

### 7.5 Вне v1

- `ActorsIndexPage` / `GET /api/actors` catalog browse
- Отображение cast на странице фильма

---

## 8. Migration and backfill

### 8.1 Alembic migration

**Revision:** `person` + `film_actor` tables, FKs, unique constraints, indexes (§4).

Порядок: `person` → `film_actor`.

### 8.2 Deploy sequence

1. `alembic upgrade head`
2. Deploy backend с `EnsureFilmCastService` (новые оценки начнут обогащаться)
3. `manage_backfill_film_cast.py` для исторических rated films
4. Deploy frontend

### 8.3 Оценка объёма

Фильмы с ≥1 rated card — подмножество каталога (~сотни–тысячи); 1 KP request / film без cast. Backfill с `--sleep 0.15` укладывается в дневной лимит KP при пакетном запуске; мониторить 429.

---

## 9. Testing

**Runner:** Docker-first — `make backend-test`, `make backend-test-unit`, `make backend-test-integration`.

### 9.1 Unit (`tests/unit/`)

| Test | Scope |
|------|-------|
| `test_parse_top_actors` | Фильтр ACTOR, порядок KP, лимит 10, billing_order, role из description |
| `test_parse_top_actors_empty` | Нет ACTOR → пустой список |
| `test_ensure_film_cast_idempotent` | Mock transport; второй `execute` — 0 KP calls |
| `test_ensure_film_cast_upsert_person` | Один person на два фильма |

### 9.2 Integration (`tests/integration/`)

| Test | Scope |
|------|-------|
| Rated card create → `film_actor` rows | `CreateUserCardService` + fake KP transport |
| Planned create → no `film_actor` | |
| Planned upgrade → cast появляется | `_finalize_upgraded_planned` path |
| KP failure on create → card OK, no cast | |
| Stats exclude planned | planned + rated same film — count только rated |
| `actor_distribution` / insights | `GET /api/users/{id}/stats` |
| `GET /api/actors/{id}` | films_count user-scoped |
| `GET /api/actors/{id}/films` | role field, pagination |
| Cards `actor_kinopoisk_id` filter | `test_profile_routes` extension |
| Backfill selection SQL | distinct films без cast |

### 9.3 Frontend

- Unit-тесты helper’ов для actor donut segment labels — только если появится отдельный mapper (не обязательны в v1).
- Manual: profile stats donut, drill-down, filter chips, public profile `userId` query.

---

## 10. Risks

| Risk | Mitigation |
|------|------------|
| KP rate limits на backfill | `--sleep`, 429 backoff, `--limit` для порционных прогонов |
| Эпизодические / дубли имён в top-10 | Принято в v1; не нормализуем |
| Фильмы без staff / без ACTOR | Без cast; stats не учитывает; повторные KP для 0-actor — см. §5.1 |
| Расхождение cast KP и «главные» актёры по мнению пользователя | Продуктово: «топ-10 по KP billing» |
| User-scoped actor API vs community directors | Документировано; разные сервисы, не переиспользовать `GetDirectorSummaryService` |
| Рост `person` / `film_actor` | Индексы §4; top-10 cap |

---

## 11. Open follow-ups (explicitly deferred)

1. **`GET /api/actors` + `ActorsIndexPage`** — глобальный каталог актёров с rated films в сообществе (symmetry с `/directors`).
2. **Monthly recap `top_actor_*`** — по аналогии с `top_director_*` в `build_monthly_recap.py`.
3. **Cast на карточке фильма** — chips актёров на detail.
4. **Negative cache** для фильмов с пустым ACTOR — снизить повторные KP.
5. **TMDB cast** — кросс-вок при гибридной metadata strategy.

---

## 12. File map (implementation checklist)

| Area | Files (new/changed) |
|------|---------------------|
| Models | `models/person.py`, `models/film_actor.py` |
| Migration | `migrations/versions/*_person_film_actor.py` |
| KP DTO | `providers/kinopoisk/kinopoisk_staff_dto.py` (+description) |
| Service | `services/cast/ensure_film_cast.py`, `parse_top_actors.py` |
| Card hook | `services/cards/create_user_card.py` |
| Stats | `services/profile/get_user_card_stats.py`, `api/profile/schemas.py` |
| Actor API | `api/actors/routes.py`, `api/actors/schemas.py`, `services/actors/*` |
| Cards filter | `api/profile/users_routes.py`, list cards service |
| Script | `manage_backfill_film_cast.py` |
| FE | `api/actorsApi.ts`, `pages/ActorDetailPage.tsx`, `ProfileStatsPanel.tsx`, `ProfileRatedCardsFilters.tsx`, `routes.tsx` |
| Tests | `tests/unit/services/cast/*`, `tests/integration/api/test_actors_routes.py`, card/stats extensions |

---

## 13. Acceptance criteria

- [ ] Rated card creation triggers cast fetch; planned does not.
- [ ] Planned→rated upgrade triggers cast fetch.
- [ ] Second rated card same film does not call KP (idempotent).
- [ ] KP error does not fail card creation.
- [ ] Stats show `actor_distribution` and `top_actor_*` without planned cards.
- [ ] `/actors/:id` shows user-scoped `films_count` and films with `role`.
- [ ] Profile cards filter by `actor_kinopoisk_id` works.
- [ ] Backfill command processes only films missing `film_actor`.
- [ ] `make backend-test` green in Docker.
