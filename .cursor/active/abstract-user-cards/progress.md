# Progress: abstract-user-cards

## Status
`completed` — user-owned card categories (shelves) verified end-to-end 2026-05-14.

## 2026-05-14: user card categories (organizational axis)

- Model `UserCardCategory`, FK `movie_card.user_card_category_id` → `user_card_category.id`; migration `a7b8c9d0e123` backfills default category **`Фильмы`** per distinct card owner and assigns all existing cards.
- API: `GET/POST /api/me/card-categories`, `PATCH /api/me/card-categories/{id}`; cards carry `category` `{id,name}` on create/detail/feed/profile list; optional `category_id` on create/patch; profile `GET /api/users/{id}/cards?category_id=` (422 if id not owned by that user).
- Services: `EnsureDefaultUserCardCategoryService`, `ResolveUserCardCategoryIdForOwnerService`, list/create/rename categories; list endpoint ensures default shelf exists.
- **Semantics:** **Categories** = per-user shelves/organization. **`provider` + `external_id`** on the card tie it to external/catalog identity for matching and resolve flows. **Tags** (mood, company, custom) remain a separate axis — not merged with categories.

### 2026-05-14 follow-up: model-layer naming + catalog provider typing

Backend ORM: `MovieCard` → `UserCard` (`movie_card` table unchanged), comments/tags/models split into `card_comment.py` / `card_tag.py` with Python `card_id` mapping legacy `movie_card_id` FK column; moods/enums moved to `card_enums.py`; `ReactionTargetKind` uses `CARD` / `CARD_COMMENT` members with values still `movie_card` / `movie_card_comment`; `FeedPost.referenced_card_id` maps DB column `referenced_movie_card_id` (JSON/API field names unchanged); `CatalogProvider(StrEnum)` on `catalog_item.provider` (VARCHAR-backed, no PostgreSQL ENUM migration). Deleted `movie_card*.py` model modules.

### 2026-05-14: card-level provider + external_id on `UserCard`

Migration `y9z0a1b2c345`: NOT NULL `movie_card.provider`, nullable `external_id`, backfill from `catalog_item` / `film.kinopoisk_id` / manual (`no_provider`), partial unique index for Kinopoisk externals. API: `CatalogProvider.no_provider`; create adds Kinopoisk `(provider, external_id)` mode; responses include `provider`/`external_id` on cards (detail, feed, profile list, patch/create); CSV export gains `provider`/`external_id` columns; `/api/catalog/resolve` rejects `no_provider`. Legacy `film_id` / `catalog_item_id` unchanged. Log: `.cursor/memory/logs/2026-05-14T163000Z-abstract-user-cards-code.md`.

### 2026-05-14: frontend + docs — provider / external_id alignment

Types (`UserCardProvider`, `MovieCard.provider` / `external_id`), `CreateMovieCardKinopoiskPayload`, manual create **`provider: no_provider`**, catalog resolve client typed **`kinopoisk` only**, KP URL helper **`kinopoiskTitleUrlFromCard`**. Log: `.cursor/memory/logs/2026-05-14T173000Z-abstract-user-cards-docs.md`.

### 2026-05-14: frontend — полки (categories) в UI и API-слое

Типы: `UserCardCategorySnippet`, `category?` на `MovieCard`, `MyUserCardCategory*` для `GET /api/me/card-categories`. `profileApi`: `getMyCardCategories`, `createMyCardCategory`, `renameMyCardCategory`, параметр списка `categoryId`; `cardApi`: опционально `category_id` на создании/PATCH. `CreateCardPage` шаг 3: полка или авто без `category_id`; медленная/ошибочная загрузка полок не блокирует сабмит. `EditMovieCardPage`: смена полки. Лента и деталь: `CardCategoryChip`. Фильтр полки в профиле через `ratedCardsListQuery.categoryId` и `enableCategoryFilter` (только «свой» список: `/profile` и свой публичный slug — без общего списка чужих полок в API). `feedQueryKeys.myCardCategoriesQueryKey`.

### 2026-05-14: final verification (categories + full surface)

- Docker: `make backend-test` → **229 passed** (~40s).
- Host: `cd frontend && npm run lint && npm run build` → **exit 0**.
- Hygiene: deleted `__pycache__` trees under `backend/src` (and bytecode caches under local `backend/.venv`; imports recompile on use). Do not commit stray `__pycache__` under `backend/src/**`.
- Logs: `.cursor/memory/logs/2026-05-14T193000Z-abstract-user-cards-test.md`, `2026-05-14T193100Z-abstract-user-cards-docs.md`.

### 2026-05-14: CreateCardPage — 4-step mobile-first wizard

- **4 шага:** (1) выбор режима «по ссылке» / «вручную» без одновременного показа обеих форм; (2) усиленный превью и подписи кнопок; (3) оценка, контекст, полка — создание полки в раскрываемой панели, ошибки только рядом с контролами полки; (4) теги, заметка, опциональная отправка подписчикам и одна кнопка «Создать карточку».
- Ошибка резолва ссылки: инлайн + действия «Создать вручную» / «Повторить по ссылке».
- Глобальный баннер `error` перенесён в начало `main` (bootstrap `filmId` / `fromCard`); остальные ошибки — контекстные (`resolveInlineError`, `shelfError`, `tagFieldError`, `submitError`, `watchlistError`).
- Verification: `cd frontend && npm run lint && npm run build` → exit 0. Log: `.cursor/memory/logs/2026-05-14T201500Z-abstract-user-cards-code.md`.

### 2026-05-14: docs + hygiene — wizard documented, caches cleared

- **Docs/process:** `docs/features/abstract-user-cards.md` and `.cursor/active/abstract-user-cards/result.md` now describe the **4-step** create flow (source choice link vs manual, manual fallback on resolve failure, shelf creation with **local validation** next to shelf controls, step 4 details + optional share). Indexed action-log fragment: `.cursor/memory/logs/2026-05-14T204500Z-abstract-user-cards-docs.md`.
- **Hygiene:** Removed every `__pycache__` directory under `backend/src` (`find backend/src -type d -name __pycache__` → **0** afterward); no stray `.pyc` under `backend/src`.
- **Frontend verification (recorded):** `cd frontend && npm run lint && npm run build` → **exit 0**.

## References

- Result and evidence: `.cursor/active/abstract-user-cards/result.md`
- Public doc: `docs/features/abstract-user-cards.md`
- Feature spec: `.cursor/features/abstract-user-cards/feature.md`
- Active plan (editable copy): `.cursor/active/abstract-user-cards/plan.md`
- Read-only planning snapshot: `.cursor/plans/abstract-user-cards-v2_6f1f3132.plan.md` — **do not edit** (workspace currently has unstashed YAML todo-status drift on this file; treat as accidental).
