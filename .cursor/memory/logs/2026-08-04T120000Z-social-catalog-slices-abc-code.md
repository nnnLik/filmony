# Action log

- **Timestamp:** 2026-08-04T12:00:00Z
- **Feature slug:** film-catalog-following-ratings, franchise-catalog-pages, catalog-browse-pages
- **Action type:** code
- **Summary:** Social Catalog slices A–C: following ratings on title pages, franchise catalog, directors/genres browse.
- **Files:** `backend/src/services/cards/list_following_ratings_for_title.py`, `backend/src/api/franchises/`, `backend/src/api/genres/`, `backend/src/services/directors/list_directors_catalog.py`, `frontend/src/components/social/FollowingRatingsPanel.tsx`, `frontend/src/pages/FranchiseDetailPage.tsx`, `frontend/src/pages/DirectorsIndexPage.tsx`, `docs/features/*.md`
- **Verification:** `make backend-test-one` for following-ratings, franchises, catalog-browse, genre_slug; `npm run lint && npm run build`
