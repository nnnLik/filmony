# Plan — film-catalog-metadata-ui

1. Introduce `FilmCatalogMetadata` orchestrator + `FilmPassportInline` + `CollapsibleFilmMetaSection`.
2. Extract display helpers to `frontend/src/lib/filmCatalogMetadataDisplay.ts`.
3. Wire `FilmDetailPage` (`variant="full"`) and `MovieCardDetailPage` (`variant="compact"`, fetch passport).
4. Add trailer labeled chip + gray placeholder when URL missing.
5. Resolve TMDB recommendations server-side (`resolve_tmdb_recommendations.py`) and render in/out-of-catalog links.
6. Tests, lint, docs closeout.
