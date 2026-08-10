# Search Catalog Redesign — Result

## Status

`completed`

## What shipped

- **Backend:** `GET /api/catalog/films` — paginated community film catalog with `sort` (popularity / avg_rating), `period` (all_time / month), optional title filter `q`, cursor pagination; films only.
- **Frontend:** Search tab redesign — `SegmentedControl` **Карточки | Люди** (default Карточки); Cards mode uses `listCatalogFilms` + infinite scroll via `CatalogFilmsSection`; People mode keeps suggestion chips + user search; optional `?tab=people` URL param.
- **Tests:** 6 integration tests for browse endpoint (sort, period, q, pagination, validation, min_ratings for avg sort).

## Changed files

### Backend

- `backend/src/services/catalog/list_catalog_films.py` — `ListCatalogFilmsService`
- `backend/src/api/catalog/routes.py` — `GET /api/catalog/films`
- `backend/src/api/catalog/schemas.py` — `CatalogFilmItemResponse`, `CatalogFilmsPageResponse`, enums
- `backend/src/tests/integration/api/test_catalog_films_list.py`

### Frontend

- `frontend/src/api/catalogApi.ts` — `listCatalogFilms`, types
- `frontend/src/pages/SearchPage.tsx` — SegmentedControl, Cards browse UI, People segment

### Docs / lifecycle

- `docs/features/search-catalog-redesign.md`
- `.cursor/features/search-catalog-redesign/feature.md`
- `.cursor/active/search-catalog-redesign/plan.md`
- `.cursor/active/search-catalog-redesign/progress.md`
- `.cursor/memory/logs/2026-08-10-search-catalog-redesign-closeout.md`

## Verification

```bash
make backend-test-one target=src/tests/integration/api/test_catalog_films_list.py
cd frontend && npm run lint && npm run build
```

- Backend: 6 passed (`test_catalog_films_popularity_all_time`, `test_catalog_films_avg_rating_excludes_low_count`, `test_catalog_films_period_month_excludes_old_cards`, `test_catalog_films_q_filters_title`, `test_catalog_films_validation_errors`, `test_catalog_films_pagination_cursor`)
- Frontend: `npm run lint` and `npm run build` pass

## Known limitations

1. **Global aggregation performance** — full-table `UserCard` aggregation for sort/period without materialized counters; may need indexes or caching at scale.
2. **`avg_rating` sort minimum** — films with fewer than **3** ratings are excluded when sorting by «Высший средний» (`min_ratings=3`); popularity sort has no minimum.
3. **`period=month` semantics** — last 30 days based on **`UserCard.created_at`**, not a separate rated-at field; applies to both `ratings_count` and `community_avg_rating`.

## Next steps (out of scope)

- Commit+push to master (user request pending)
- Materialized popularity counters if browse latency becomes an issue
