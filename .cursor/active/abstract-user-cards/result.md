# Result: abstract-user-cards

## Status
`completed`

## What was implemented

- **Backend — cards API and services:** `POST /api/cards` accepts `catalog_item_id`, manual display fields, and **Kinopoisk `provider` + `external_id`**; maps `CatalogItemNotFoundError` → 404; card list/detail/feed payloads include catalog + display fields and required **`provider`** + nullable **`external_id`**; optional **`category_id`** on create/patch; responses include embedded **`category`** `{id, name}` where applicable; shared card response helper normalizes empty title to `Untitled`. Services updated: create (film / catalog / **Kinopoisk external** / manual **`no_provider`** paths), details, feed hydration, profile movie-card lists, inline `⟦c⟧` resolution (`coalesce` title), following-ratings (match by `film_id` or `catalog_item_id`; empty list for pure manual anchor), inline picker.
- **Backend — user-owned card categories (shelves):** Model `UserCardCategory`; `UserCard.user_card_category_id` (migration **`a7b8c9d0e123`**) with backfill of default shelf **`Фильмы`** per owner. **`GET` / `POST` / `PATCH`** `/api/me/card-categories`; **`ResolveUserCardCategoryIdForOwnerService`** / **`EnsureDefaultUserCardCategoryService`**. Profile list supports **`?category_id=`**; **422** when the category does not belong to the profile user being viewed.
- **Backend — catalog:** `POST /api/catalog/resolve` (`provider` + `url`, first provider `kinopoisk`; **`no_provider` rejected**) via `ResolveCatalogItemService`; router registration in `api/router.py`.
- **Backend — Python ORM (generic card naming, 2026-05-14):** Persistence stays on legacy table/column names for compatibility; the **Python** layer uses card-oriented types and modules only. `UserCard` maps `__tablename__ = 'movie_card'`. `CardComment` / `CardTag` map `movie_card_comment` / `movie_card_tag` with `card_id` ↔ `movie_card_id` column aliases where applicable. Card-facing StrEnums live in `card_enums.py` (`CardCompany`, moods). **`CatalogProvider(StrEnum)`** (`kinopoisk`, …) backs `catalog_item.provider` via SQLAlchemy `Enum(native_enum=False)` — no PostgreSQL ENUM migration. **`backend/src/models/movie_card*.py` removed**; replacements: `user_card.py`, `user_card_category.py`, `card_comment.py`, `card_tag.py`, `card_enums.py`. `ReactionTargetKind` exposes `CARD` / `CARD_COMMENT` **members** whose **stored values** remain `movie_card` / `movie_card_comment` until a dedicated API/storage migration.
- **Frontend:** `UserCardProvider` on `MovieCard` (`kinopoisk` | `no_provider`) and nullable **`external_id`**; **`category`** / shelf picker on create and edit; **`CardCategoryChip`** on feed and detail; profile rated list filter by **`categoryId`** (own profile / own public slug only — no third-party shelf catalog API). **`catalogApi`** exposes **`CatalogResolveRequestProvider`** = `kinopoisk` only; **`cardApi`** supports **`category_id`** on create/patch; **`profileApi`** lists/creates/renames **`/api/me/card-categories`**.
- **Frontend — `CreateCardPage` (mobile-first, 4 steps):** (1) **Source choice** — Kinopoisk URL vs **manual** (`SourceMode`: `pick` → `url` or `manual`); the two heavy forms are **not** shown at once. (2) **Verify title** — Stronger preview/copy for primary actions. (3) **Rating and shelf** — Score, company/moods, shelf picker; **new shelf** in an expandable panel with **errors scoped to shelf controls** (slow category fetch does not block submit). (4) **Details and share** — Custom tags, watch note, optional follower share, single **Create card** action. **Resolve** failures: inline error plus **Create manually** / **Retry with link**. **`filmId` / `fromCard` bootstrap** errors: global banner at the top of `main`; other validation uses contextual state (`resolveInlineError`, `shelfError`, `tagFieldError`, `submitError`, `watchlistError`).
- **Tests:** `test_cards_routes.py` (category CRUD + card `category_id` + cross-user rejection), `test_profile_routes.py` (`category_id` filter), `test_movie_card_catalog_schema.py` (FK), shared test helper `tests/support/user_card_category.py`; suite-wide fixtures updated in feed/search/community/export tests. Full suite passes (see verification).

**Conceptual split (product + API):**

- **Categories** — user-owned shelves for organizing cards; not shared across users; unrelated to Kinopoisk/catalog matching.
- **`provider` / `external_id` (and `catalog_item_id`)** — canonical / external matching and resolve; distinct from shelves.
- **Tags** — mood, company, custom tags; remain separate from categories.

Schema/migrations (`CatalogItem`, nullable `movie_card.film_id`, `catalog_item_id`, display columns, **`movie_card.provider` / `external_id`** — `y9z0a1b2c345`) and model tests were delivered in earlier increments; referenced in progress history.

## Intentional legacy naming (DB / API)

ORM `__tablename__`, index names, FK columns (`movie_card_id`, …), and several **JSON field names** (`film_*`, nullable `film_id`, `referenced_movie_card_id` in DB for feed posts) stay **film-/movie-prefixed** for backward compatibility with existing clients and databases. **Only** the Python model **module and class names** are generic (`UserCard`, `CardComment`, …); no requirement to rename the physical schema or public API in this slice.

## Changed files (this feature surface)

**Backend**

- `backend/src/models/user_card.py`, `user_card_category.py`, `card_comment.py`, `card_tag.py`, `card_enums.py`, `catalog_item.py` (`CatalogProvider`), `reaction_target_kind.py`, `feed_post.py`, `__init__.py`
- `backend/src/migrations/versions/a7b8c9d0e123_user_card_category.py`, `y9z0a1b2c345_movie_card_provider_subject.py`
- `backend/src/api/cards/routes.py`, `backend/src/api/cards/schemas.py`
- `backend/src/api/profile/me_routes.py`, `users_routes.py`, `schemas.py`
- `backend/src/api/catalog/routes.py`, `backend/src/api/catalog/schemas.py`
- `backend/src/api/feed/routes.py`, `backend/src/api/feed_posts/routes.py`, `schemas.py`, `backend/src/api/router.py`
- `backend/src/services/cards/*`, `backend/src/services/catalog/*`, `backend/src/services/profile/list_user_movie_cards.py`, `backend/src/services/user_card_categories/*`
- `backend/src/tests/api/test_cards_routes.py`, `test_profile_routes.py`, `test_feed_posts_routes.py`, `test_film_community_routes.py`, `test_search_routes.py`, `test_movie_card_feed_recommendation.py`, `test_following_ratings_for_movie_card.py`, `test_me_cards_export_csv.py`, `test_movie_card_catalog_schema.py`, `backend/src/tests/support/user_card_category.py`

**Frontend**

- `frontend/src/api/cardApi.ts`, `frontend/src/api/catalogApi.ts`, `frontend/src/api/profileApi.ts`, `frontend/src/api/profileTypes.ts`
- `frontend/src/lib/movieCardDisplay.ts`, `frontend/src/lib/openExternalUrl.ts`, `frontend/src/lib/ratedCardsListQuery.ts`, `frontend/src/feed/feedQueryKeys.ts`
- `frontend/src/components/cards/CardCategoryChip.tsx`, `frontend/src/components/feed/FeedCard.tsx`, `frontend/src/components/profile/ProfileRatedCardsFilters.tsx`
- `frontend/src/pages/CreateCardPage.tsx`, `EditMovieCardPage.tsx`, `MovieCardDetailPage.tsx`, `ProfilePage.tsx`, `PublicProfilePage.tsx`

**Process / docs**

- `.cursor/active/abstract-user-cards/progress.md`, `.cursor/active/abstract-user-cards/result.md`
- `docs/features/abstract-user-cards.md`
- `.cursor/memory/logs/action-log.md`, fragments under `.cursor/memory/logs/` (including `2026-05-14T204500Z-abstract-user-cards-docs.md`)

## Verification

| Command | Result |
|--------|--------|
| `make backend-test` | **229 passed** (Docker `backend`, ~40s — **2026-05-14** final pass) |
| `make backend-lint` | Not run this session (prior slices clean); run before merge if desired |
| `cd frontend && npm run lint && npm run build` | **Exit 0** — ESLint clean, `tsc -b && vite build` succeeded (**2026-05-14**, including post–4-step wizard pass) |

**Structural check:** no `backend/src/models/movie_card*.py` files in tree (generic model modules only).

**Cache hygiene (2026-05-14):** no `__pycache__` directories under `backend/src` after cleanup (`find` verification).

Focused category coverage: `test_cards_routes.py` (`/api/me/card-categories`, create/patch `category_id`), `test_profile_routes.py` (`?category_id=` filter + 422), `test_movie_card_catalog_schema.py` (`user_card_category_id` FK).

## Known limitations / next steps

- Legacy response fields (`film_*`, `film_id`) retained for transitional clients; eventual removal after adoption.
- Service module filenames and some stats DTOs remain film/movie-named; rename or generalize when a dedicated refactor milestone lands.
- Pure manual cards: following-ratings aggregation intentionally empty (no shared anchor).
- **Profile shelf filter:** scoped to contexts where the viewer can infer valid `category_id` values (own profile UX); strangers listing another user’s cards filter by numeric id without a “list their shelves” API — callers must use ids they already know or omit filter.
- **Repo hygiene:** do not commit `__pycache__` under `backend/src/`; bytecode under a local `.venv` is harmless to delete (reimports recompile).
- **Planning snapshot:** `.cursor/plans/abstract-user-cards-v2_6f1f3132.plan.md` — do not edit per workspace policy; treat YAML drift as local only.

## Plan / todos

Implementation matches the Universal User Cards plan intent including user-owned categories and automated verification. External read-only plan file may still show YAML `verification: in_progress` in a dirty working tree; functional verification for this increment is **done** per table above.
