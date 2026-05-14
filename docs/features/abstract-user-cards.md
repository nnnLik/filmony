# Feature: Universal User Cards (`abstract-user-cards`)

## Summary

The product shifts from a **film- and Kinopoisk-centric** card model to **card-first universal user cards**. The persisted row remains `movie_card` with stable ids; optional linkage uses `catalog_item` (provider-discriminated canonical metadata, first provider `kinopoisk`) plus **user-owned display fields** (`display_title`, `display_cover_url`, `display_summary`) so manual cards and transitional reads stay coherent.

## User-owned categories (“shelves”)

- **Purpose:** Per-user **organization** of cards into named shelves. Each owner has at least one category (migration **`a7b8c9d0e123`** seeds default **`Фильмы`** and assigns existing cards).
- **Persistence:** Table `user_card_category`; FK **`movie_card.user_card_category_id`** (NOT NULL after migration).
- **API:** `GET` / `POST` `/api/me/card-categories`, `PATCH` `/api/me/card-categories/{id}`. Cards expose embedded **`category`** `{ id, name }` on create, detail, feed, and profile list payloads. **`category_id`** is optional on **`POST /api/cards`** and **`PATCH`**.
- **Profile filter:** `GET /api/users/{id}/cards?category_id=` filters to cards in that shelf; **422** if `category_id` is not owned by user **`id`**.
- **Frontend:** Shelf picker on create/edit, **`CardCategoryChip`** on feed/detail, rated-list filter where the viewer manages their own shelves (see app routing — not a public “browse all shelves” API for arbitrary users).

**Not the same as tags or externals:**

- **`provider` / `external_id`** (and `catalog_item_id`) describe **matching** to catalog or external identities — independent of which shelf the user put the card in.
- **Tags** (company, moods, custom tags) are a **separate** labeling axis; categories do not replace tags.

## Current implementation (2026-05)

- **Schema:** `catalog_item`; nullable `movie_card.catalog_item_id` and `movie_card.film_id`; partial uniques for duplicates; migrations `u1v2w3x4y890`, `w3x4y5z6a012` (display backfill), **`a7b8c9d0e123`** (categories), **`y9z0a1b2c345`** (`provider` / `external_id` on cards). Model tests: `backend/src/tests/models/test_movie_card_catalog_schema.py`.
- **Python ORM (generic naming):** Types live in `user_card.py` (`UserCard`), `user_card_category.py`, `card_comment.py` (`CardComment`), `card_tag.py` (`CardTag`), `card_enums.py` (card StrEnums). There are **no** `movie_card*.py` modules under `backend/src/models/`. **`CatalogProvider(StrEnum)`** in `catalog_item.py` types `catalog_item.provider` (VARCHAR-backed enum in SQLAlchemy, not a Postgres ENUM type).
- **Naming split:** **Database and HTTP JSON** keep legacy `movie_*` / `film_*` names where they already shipped (tables, columns, deprecated film fields on card DTOs) so existing clients and migrations stay stable. **Python** class and module names are **card-generic** because comments, tags, moods, and shelves apply to any card, not only films.
- **Writes:** `POST /api/cards` — film-backed (`film_id` / `kinopoisk_id`, optional `catalog_item_id`), catalog-only (`catalog_item_id`), Kinopoisk by **`provider: kinopoisk`** + **`external_id`**, or manual (**`provider: no_provider`**, `display_title`, `external_id` null); optional **`category_id`** validated as owned by the actor; validation and 409 on duplicate partial unique.
- **Reads:** Card detail, feed items, profile grids/lists, inline picker, inline card refs, and following-ratings honor nullable film joins, catalog/manual display fields, **`category`** snippet, **`provider`** / **`external_id`**. Deprecated `film_*` populated when a `Film` row exists; otherwise sensible fallbacks (e.g. display title).
- **Resolve:** `POST /api/catalog/resolve` with `{ provider, url }` (Kinopoisk first) upserts `CatalogItem` + nested film payload; **`no_provider` is rejected** on this route; `POST /api/films/resolve` unchanged for legacy clients.
- **Frontend:** Types and create wizard (`catalogApi` — catalog resolve typed as **`kinopoisk` only** + legacy film resolve + manual path with explicit **`provider: no_provider`**); `MovieCard` includes **`provider`** / **`external_id`** / optional **`category`**; Kinopoisk deep link via **`kinopoiskNumericIdFromCard`** (`film_kinopoisk_id` or numeric **`external_id`**).

### Create card wizard (`CreateCardPage`, 2026-05-14)

Mobile-first **four-step** flow (`frontend/src/pages/CreateCardPage.tsx`):

1. **How to add the title** — User picks **Kinopoisk link** or **manual** entry (modes `pick` → `url` / `manual`); URL and manual forms are **not** shown simultaneously.
2. **Verify the title** — Confirmation step with clear preview and actions before continuing.
3. **Rating and shelf** — Score, company/moods, shelf selection; **creating a new shelf** lives in an expandable panel with **validation/errors next to shelf controls** (failed or slow category loads do not hard-block finishing the card).
4. **Details and send** — Custom tags, watch note, optional **share to followers**, single primary **Create card** submit.

**Resolve failures** (bad/missing Kinopoisk URL): inline message with **Create manually** and **retry by link**. Query-param bootstrap (`filmId`, `fromCard`) surfaces a **banner at the top of the main** content; other errors stay contextual (resolve, shelf, tags, submit, watchlist).

## API and compatibility

New fields: `catalog_item_id`, `display_title`, `display_cover_url`, `display_summary`, **`provider`**, **`external_id`**, **`category`** / **`category_id`**. Deprecated `film_*` / nullable `film_id` remain for legacy clients until a dedicated cleanup milestone.

- **CSV export** of my cards includes **`provider`** and **`external_id`** columns for compatibility with spreadsheets and downstream tools.

## Roadmap / cleanup

- Remove or narrow deprecated `film_*` once all clients consume card-first fields.
- Additional catalog providers beside Kinopoisk.
- Align any remaining statistics DTOs with explicit display metadata if needed.
- Optional: rename remaining backend **service filenames** from `movie_card` to a neutral prefix when a broad refactor is scheduled (behavior unchanged).
- Optional: public or friend-visible shelf discovery if product needs browsing another user’s category names safely.

## Verification

- Backend (Docker): `make backend-test` — **229 passed** (**2026-05-14** recorded run).
- Frontend: `cd frontend && npm run lint && npm run build` (ESLint + `tsc -b && vite build` clean — **2026-05-14**).
- Hygiene: generated **`__pycache__`** directories under `backend/src` removed locally (`find backend/src -type d -name __pycache__` → 0); do not commit bytecode under source trees.

Evidence and delivery notes: `.cursor/active/abstract-user-cards/progress.md`, `.cursor/active/abstract-user-cards/result.md`, `.cursor/memory/logs/2026-05-14T193000Z-abstract-user-cards-test.md`, `.cursor/memory/logs/2026-05-14T204500Z-abstract-user-cards-docs.md` (create-flow docs + hygiene).

## References

- Feature spec: `.cursor/features/abstract-user-cards/feature.md`
- Active delivery notes: `.cursor/active/abstract-user-cards/result.md`
- Read-only planning snapshot: `.cursor/plans/abstract-user-cards-v2_6f1f3132.plan.md`
