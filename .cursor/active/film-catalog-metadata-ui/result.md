# Result — film-catalog-metadata-ui

Status: **completed** (2026-08-15T010500Z)

## Implemented

- Unified passport UI on film detail and movie card pages with compact/full variants.
- Colored KP/IMDb ratings, duration, age limit, slogan, trailer chip or «Трейлер пока недоступен».
- Collapsible «Где смотреть» / «Похожие» on film pages; horizontal similar scroll on full layout.
- Similar titles navigate to in-catalog film pages or search when not in DB.

## Changed files

- `frontend/src/components/films/FilmCatalogMetadata.tsx`
- `frontend/src/components/films/FilmPassportInline.tsx`
- `frontend/src/components/films/CollapsibleFilmMetaSection.tsx`
- `frontend/src/lib/filmCatalogMetadataDisplay.ts`
- `frontend/src/pages/FilmDetailPage.tsx`
- `frontend/src/pages/MovieCardDetailPage.tsx`
- `backend/src/services/films/resolve_tmdb_recommendations.py`
- `backend/src/api/films/mappers.py` (recommendation items in API)

## Verification

- `cd frontend && npm run lint && npm run build`
- `cd frontend && npm run test -- --run src/lib/__tests__/filmCatalogMetadataDisplay.test.ts`
- `make backend-test-one target=src/tests/unit/services/films/test_resolve_tmdb_recommendations.py`

## Known limitations

- Out-of-catalog similar titles open search, not external TMDB pages.
- Passport ratings depend on KP/TMDB sync and backfill on prod films.

## Next steps

- Run KP passport backfill for rated films missing `rating_kinopoisk`.
