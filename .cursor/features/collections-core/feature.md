# Collections Core

## Metadata

| Field | Value |
|-------|-------|
| Feature slug | `collections-core` |
| Status | `in_progress` |
| Stack | fullstack |
| Created | 2026-08-07 |

## Problem

В Filmony нет **курируемых подборок фильмов** с персональным прогрессом: пользователь не видит, сколько фильмов из «Letterboxd Top 500» или каталога «Оскар 2026» он уже **оценил**, и не получает награду за полное прохождение подборки.

> **Важно:** доменная сущность **Collection** — это наша подборка (curated set of films). **Не путать** с TMDB `collection` / franchise metadata на модели `Film`.

## Goal

Ввести домен **Collection** (v1: `evergreen` + `seasonal`), засеять статический Top 500 и первый Oscar-каталог, считать прогресс по **оценённым** карточкам, отдавать API и UI списка/детали, при 100% — эмитить событие завершения для sibling-фичи достижений.

## Scope

### In scope (v1)

- Модели и миграции: `Collection`, `CollectionFilm`, `UserCollectionProgress` (или эквивалент), enum `CollectionKind` (`evergreen` | `seasonal`).
- **Evergreen:** `letterboxd-top-500` — статический seed из CSV/JSON; **после импорта состав не обновляется автоматически** (никаких cron/sync задач для evergreen).
- **Seasonal:** Oscar year catalogs, напр. `oscars-2026`, `oscars-2027` — новые сезонные подборки создаются/активируются Celery-задачей; расписание — **внешний crontab на хосте** (Celery Beat **не** в репозитории); crontab документируется в docstring модуля задачи (паттерн `backend/src/tasks/monthly_recap.py`).
- Seed: идентичность фильма — **`kinopoisk_id` primary**; строки seed мапятся через **`imdb_id`** → существующие resolve/sync паттерны (Kinopoisk search + `SyncFilmFromTmdbService` / film upsert).
- **Progress:** фильм засчитывается, если у пользователя есть **UserCard** с `is_planned=false` и `rating >= 1.0` (то же правило, что taste-quiz gate — см. `meaningful_rated_cards_stmt` в `backend/src/services/taste_quiz/card_pool.py`). **Watchlist / planned cards не считаются.**
- При **100% progress** → unlock collection completion **reward/achievement**. Детали rarity/pins/UI achievement — sibling `achievements-rarity-profile-pins`; **эта фича** обязана экспонировать completion **event/hook** или создать минимальный `UserAchievement` stub с задокументированной зависимостью.
- Public/authenticated API: list collections (with viewer progress), collection detail header, **paginated** film list with `viewer_has_rated`; **`content_updated_at`** on list + detail (when collection membership/metadata last changed — not user progress).
- **Profile «Коллекции» tab:** always present on profile from launch; **empty until** the user pins ≥1 global collection; pinned set visible on own and other users' profiles (viewer sees **profile owner's** pins + **owner's** progress on those collections).
- **Pin/unpin collections:** per-user preference (`UserCollectionPin` join); button «Закрепить» / «Открепить» on collection detail (and/or list); v1 pin limit **max 10** (documented in AC; may raise later).
- **Navigation (app-level discovery):** отдельная вкладка bottom nav **«Коллекции»** → `/collections` — глобальный каталог active подборок; **не путать** с profile tab «Коллекции» (закреплённые подборки пользователя).
- **Frontend UX:** экран списка подборок → экран детали с **плоским** списком карточек фильмов, визуальным статусом **оценён / не оценён**, infinite scroll для больших подборок; tap фильма → существующий `/films/:filmId`.
- Backend pytest (unit + integration) и frontend lint/build; тесты **Docker-first** (`make backend-test`, см. `.cursor/tech.md`).

### Out of scope (v1)

- **Oscar badges на карточках фильмов** — sibling `film-award-badges`; бейджи **не** FK-связаны с `Collection`. После релиза `film-award-badges` бейджи **могут** появиться на общем экране фильма; опционально — на строках коллекции, но **не** входят в AC `collections-core`.
- **«My film of the year»** pick после 100% — follow-up (отдельная фича / v2).
- Авто-обновление состава Letterboxd Top 500.
- Celery Beat в репозитории.
- Gamification rarity tiers, **achievement** profile pins (1–3 unlocked achievements), полный achievement catalog UI (делегируется `achievements-rarity-profile-pins`). **Collection pins** (this feature) — отдельная сущность и profile tab; обе могут сосуществовать на профиле (разные вкладки/секции).

## Functional Requirements

### FR-1 Collection entity

- `Collection`: `slug` (unique), `kind`, `title`, `description`, `season_year` (nullable, для seasonal), `is_active`, `film_count` (denormalized или computed), `created_at`, **`content_updated_at`** (see FR-10).
- **`content_updated_at`:** last time **collection content or catalog metadata** changed (membership, title, description, `is_active`, `film_count` refresh from seed/sync). **Not** bumped by per-user progress (`UserCollectionProgress`) or pin/unpin actions.
- `CollectionFilm`: `(collection_id, film_id)` unique; optional `sort_order`, optional seed `imdb_id` audit field.
- Evergreen slug example: `letterboxd-top-500`.
- Seasonal slug pattern: `oscars-{year}`.

### FR-2 Progress

- Per user per collection: `rated_count`, `total_count`, `progress_percent`, `completed_at` (nullable).
- Пересчёт прогресса: on-demand в read path и/или invalidate on UserCard rating create/update (service hook).
- Completion: idempotent — при первом достижении 100% записать `completed_at` и вызвать completion hook.
- **Eventual consistency:** после оценки на экране фильма прогресс может обновиться при возврате на экран коллекции (refetch on focus / invalidate query) — синхронный push не обязателен.

### FR-3 Completion hook / achievement dependency

- `CompleteCollectionService` (или nested helper) при первом completion:
  - emit domain event / call `GrantCollectionAchievementService` stub;
  - achievement `slug` TBD, e.g. `collection-complete:{collection_slug}`;
  - **Dependency:** полная модель `UserAchievement`, rarity, profile pin — **`achievements-rarity-profile-pins`**. До неё — stub table или no-op adapter с контрактом, зафиксированным в `plan.md`.

### FR-4 Seed & resolve

- Management command / script: `manage_seed_collection.py` (или аналог) для импорта Top 500 и Oscars 2026.
- Для каждой seed-строки: normalize `imdb_id` → resolve/create `Film` via existing Kinopoisk/TMDB pipeline; persist `CollectionFilm`.
- Evergreen import **one-shot**; повторный запуск только с явным `--force` (documented).

### FR-5 Seasonal Celery task

- `backend/src/tasks/ensure_seasonal_collections.py` (name TBD):
  - ensure/create active `oscars-{current_or_next_year}` collection from seed manifest;
  - docstring documents host crontab (e.g. annually or before Oscar season);
  - register via `register_tasks` in `celery_app.py` (см. `docs/features/celery-redis-workers.md`).

### FR-6 API (English contracts)

- `GET /api/collections` — все **active global** collections; optional `kind` filter; для auth-пользователя — `viewer_progress` (`rated_count`, `total_count`, `progress_percent`) и **`is_pinned: bool`** (whether current user pinned this collection); each item includes **`content_updated_at`** (ISO 8601).
- `GET /api/collections/{slug}` — metadata (`title`, `description`, `kind`, `film_count`, **`content_updated_at`**, …) + `viewer_progress` + **`is_pinned`** if auth; **без** полного списка фильмов (header-only).
- `GET /api/collections/{slug}/films` — **paginated** flat film list: film summary fields + `viewer_has_rated: bool` (auth) or omitted/false for anonymous; query params `limit` + `cursor` or `offset` (choose one in implementation; support large collections ~500 items).
- `GET /api/me/collections` — (optional convenience) all collections with user progress summary (auth); may mirror list endpoint with required auth.
- `POST /api/me/collection-pins/{slug}` — pin global collection for current user (idempotent); enforce **max 10** pins → `409` or `422` when limit exceeded.
- `DELETE /api/me/collection-pins/{slug}` — unpin (idempotent).
- `GET /api/profiles/{userId}/collections` — **profile owner's pinned collections** for the profile «Коллекции» tab: ordered list of `{ slug, title, short description, content_updated_at, owner_progress }` where `owner_progress` is the **profile owner's** rated/total/percent (same rated-only rule). Empty array when owner has zero pins. Auth optional; progress fields require viewer auth or public-profile rules consistent with existing profile API.

Schemas in `backend/src/api/collections/schemas.py`; thin routes in `backend/src/api/collections/routes.py` (+ profile pin routes or `backend/src/api/profile/` extension — pick one in `plan.md`).

### FR-10 Collection `content_updated_at`

- Persist **`content_updated_at`** on `Collection` — semantic «last collection catalog change», distinct from generic ORM `updated_at` if both exist.
- **Bump `content_updated_at` when:**
  - seed/import creates or updates collection metadata or membership (`CollectionFilm` add/remove/reorder);
  - Celery `ensure_seasonal_collections` changes Oscar membership or collection metadata;
  - manual ops re-seed with `--force` or admin metadata edit.
- **Do not bump when:**
  - user rates/unrates a film (`UserCollectionProgress` recalc);
  - user pins/unpins a collection (`UserCollectionPin`).
- **Evergreen Top 500:** set at seed/import time; stays fixed unless ops manually re-imports seed.
- **Seasonal Oscar:** bumps when ensure/sync changes nominees/winners or catalog fields.
- Expose in **`GET /api/collections`** and **`GET /api/collections/{slug}`**; optional display in list/detail UI (at minimum API-ready).

### FR-11 Profile collection pins & «Коллекции» tab

- **`UserCollectionPin`:** `(user_id, collection_id)` unique; optional `sort_order` (pin order on profile tab); `pinned_at` timestamp.
- User can **pin/unpin** any **active global** collection via UI control **«Закрепить»** / **«Открепить»** (collection detail header primary; list row optional).
- **Pin limit v1:** **max 10** pinned collections per user (reasonable default vs unlimited; document in AC; achievements sibling uses 1–3 for **achievement** pins — different entity).
- **Profile UI:** add **«Коллекции»** tab on profile screen — **always visible from launch**, even when empty.
  - **Empty state:** tab shows empty placeholder until user pins ≥1 collection (no hidden tab).
  - **With pins:** each row/card — title, short description, **profile owner's** progress % (+ rated/total when viewing own profile).
  - **Viewing another user's profile:** show **their** pinned set and **their** progress on those collections (not viewer's progress).
- **Distinct from app nav:** Bottom nav **«Коллекции»** (`/collections`) = global discovery catalog; profile tab **«Коллекции»** = curated showcase of pinned collections only.
- **Cross-reference:** sibling **`achievements-rarity-profile-pins`** pins **achievements** (completion badges, 1–3 slots); this feature pins **collections** (catalog entities). Both may appear on profile in separate tabs/sections — no shared pin table.

### FR-7 App navigation & global discovery tab

- Новая вкладка в `BottomNav`: label **«Коллекции»**, route `/collections` (under `AppShell`, alongside Лента / Поиск / Профиль).
- **App-level discovery tab** показывает **глобальные active** подборки (Letterboxd Top 500, Oscars 2026, …) — отдельно от genres/directors browse в Поиске и **отдельно** от profile tab «Коллекции» (FR-11/FR-12), где только закреплённые пользователем подборки.
- Icon: `Layers` or `LibraryBig` from `lucide-react` (tree-shakeable import), стиль как у существующих nav icons.

### FR-8 Collections list screen

- Route: `/collections` → `CollectionsIndexPage`.
- Каждая строка/карточка подборки: **title**, **short description** (или snippet), **progress %**; ideally **rated_count / total_count**.
- Tap → navigate to `/collections/:slug`.
- Loading, empty (no active collections), error states.

### FR-9 Collection detail screen

- Route: `/collections/:slug` → `CollectionDetailPage`.
- **Header:** collection title, short description, user **progress %** and **rated/total** counts (auth only; guest sees metadata without personal progress).
- **Body:** **flat** list of film rows — **no nested categories** or grouped sections in v1.
- Each row: poster, title, year (reuse patterns from `CatalogRatedFilmRow` / existing film list rows); clear **оценён / не оценён** for current user.
- **Rated vs unrated visual** (concrete v1 spec):
  - **Rated:** full opacity; small mint `CircleCheck` badge (lucide) overlay on poster corner; optional secondary line «Оценён» in `--tgui--hint_color`.
  - **Unrated:** poster at `opacity-60`; text «Не оценён» in `--tgui--hint_color`; no checkmark.
- Tap film row → `Link` to existing **`/films/:filmId`** (`FilmDetailPage`) — reuse community film page; **no** parallel collection-specific film detail.
- **Infinite scroll:** load films page-by-page as user scrolls (IntersectionObserver sentinel + `@tanstack/react-query` `useInfiniteQuery`, same family as `useUserCardsInfiniteQuery` / profile watchlist panels); initial page size ~20–30.
- On return from film page: refetch collection progress + visible film rated flags (query invalidation or `refetchOnWindowFocus`).

### FR-12 Profile «Коллекции» tab UI

- Profile screen gains tab **«Коллекции»** alongside existing profile tabs — **always rendered**, never conditional on pin count.
- **Empty:** dedicated empty copy (e.g. «Закрепите подборки, чтобы показать их здесь») + optional CTA link to app `/collections` discovery tab.
- **Non-empty:** list pinned collections in `sort_order`; tap → `/collections/:slug`.
- Own profile: show pin management elsewhere (collection detail «Закрепить»/«Открепить»); tab is read-only display of pinned set + own progress.
- Public/other profile: read-only pinned list + **owner's** progress per row.

## Acceptance Criteria

- [ ] Alembic migration creates `Collection` (with **`content_updated_at`**), `CollectionFilm`, `UserCollectionProgress`, **`UserCollectionPin`** with constraints and indexes.
- [ ] **`content_updated_at`** bumps on seed/import and seasonal Celery membership/metadata changes; **does not** bump on user progress recalc or pin/unpin.
- [ ] Evergreen `letterboxd-top-500` **`content_updated_at`** equals seed/import time and stays unless manual re-seed.
- [ ] `GET /api/collections` and `GET /api/collections/{slug}` expose **`content_updated_at`**; auth responses include **`is_pinned`** where applicable.
- [ ] Pin/unpin API: `POST/DELETE /api/me/collection-pins/{slug}`; max **10** pins enforced with clear 4xx.
- [ ] `GET /api/profiles/{userId}/collections` returns owner's pinned collections + **owner's** progress; empty array when no pins.
- [ ] Profile **«Коллекции»** tab always exists; empty until ≥1 pin; shows owner's pinned set and progress (own vs other profile rules per FR-11/FR-12).
- [ ] Collection detail (and/or list) shows **«Закрепить»** / **«Открепить»** for authenticated users.
- [ ] Profile collection pins documented as **distinct** from achievement profile pins in **`achievements-rarity-profile-pins`** (cross-ref in both feature docs).
- [ ] Seed imports `letterboxd-top-500` (~500 films) and `oscars-2026` via `imdb_id` → `Film.kinopoisk_id` resolve; evergreen not auto-updated after seed.
- [ ] Progress uses `UserCard.is_planned=false` AND `UserCard.rating >= 1.0` only; watchlist excluded.
- [ ] `GET /api/collections` returns active global collections; auth response includes per-collection viewer progress.
- [ ] `GET /api/collections/{slug}` returns header metadata + viewer progress; does not require loading all films.
- [ ] `GET /api/collections/{slug}/films` returns paginated film summaries with `viewer_has_rated` for authenticated users; supports Top 500 scale.
- [ ] First-time 100% completion sets `completed_at` and invokes documented achievement hook/stub (dependency on `achievements-rarity-profile-pins` noted in code + docs).
- [ ] Celery `ensure_seasonal_collections` task registered; crontab documented in module docstring (no Beat in repo).
- [ ] Oscar film badges **not** implemented here; no FK from badges to collections.
- [ ] Bottom nav includes **«Коллекции»** tab linking to `/collections` (**app-level discovery** — not the profile pinned tab).
- [ ] Collections list screen shows title, description/snippet, progress % (and counts when auth).
- [ ] Collection detail shows header progress, flat film list with rated/unrated visual distinction, infinite scroll pagination.
- [ ] Film row tap navigates to existing `/films/:filmId`; progress refreshes after rating on film page (eventual consistency acceptable).
- [ ] Backend tests: progress math, completion idempotency, seed resolve mocks, API integration including pagination + `viewer_has_rated`, **`content_updated_at`** bump rules, pin limit + profile pinned collections endpoint.
- [ ] Frontend list/detail pages render per spec; profile **«Коллекции»** tab (empty + populated); pin/unpin control; `npm run lint && npm run build` pass.
- [ ] Feature docs published at closeout: `docs/features/collections-core.md`.

## Constraints

- **Layer boundaries:** routes thin; business logic in `@dataclass` services with `build()` / `execute()` per backend standards.
- **Film identity:** `kinopoisk_id` remains primary catalog key; seed input may only provide `imdb_id`.
- **Collection ≠ TMDB collection:** do not reuse `Film.franchise_key` / TMDB collection IDs as collection membership.
- **Workers:** Celery + Redis per `docs/features/celery-redis-workers.md` and `.cursor/tech.md` — **no Celery Beat** in repo.
- **Tests:** Docker-first — `make backend-test`, `make backend-test-one target=…` for scoped runs.

## References

### Sibling feature slugs

| Slug | Relationship |
|------|----------------|
| `achievements-rarity-profile-pins` | Full achievement model, rarity, **achievement** profile pins (1–3 slots); consumes collection completion hook. **Not** collection pins — see FR-11 |
| `film-award-badges` | Oscar/nomination badges on films — **out of scope**, not FK-tied to collections; may appear on film page / optionally on collection rows later |
| `tmdb-film-integration` | IMDB crosswalk + TMDB enrichment for seed resolve |
| `profile-gamification-stamps` | Related gamification patterns (achievements, passport) |

### Docs & tech

- [`docs/features/celery-redis-workers.md`](../../../docs/features/celery-redis-workers.md) — worker registration, no Beat
- [`.cursor/tech.md`](../../tech.md) — Docker stack, `celery-worker`, test commands
- [`backend/src/tasks/monthly_recap.py`](../../../backend/src/tasks/monthly_recap.py) — crontab docstring pattern

### Code touchpoints

- Film model: [`backend/src/models/film.py`](../../../backend/src/models/film.py)
- Meaningful rated gate: [`backend/src/services/taste_quiz/card_pool.py`](../../../backend/src/services/taste_quiz/card_pool.py) (`UserCard.rating >= 1.0`, `is_planned=false`)
- UserCard model: `backend/src/models/user_card.py`
- Celery app: `backend/src/celery_app.py`
- Bottom nav: `frontend/src/components/navigation/BottomNav.tsx`
- Routes: `frontend/src/routes.tsx` (`/films/:filmId` → `FilmDetailPage`)
- Film row reference: `frontend/src/components/catalog/CatalogRatedFilmRow.tsx`
