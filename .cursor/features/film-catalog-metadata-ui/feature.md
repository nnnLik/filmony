# Film catalog metadata UI

## Metadata
- Feature slug: `film-catalog-metadata-ui`
- Status: done
- Created at: 2026-08-15

## Goal
Make KP/TMDB passport data readable on film and card pages: compact layout, colored ratings, trailer affordance, collapsible providers/similar blocks, and clickable similar titles.

## Acceptance criteria
- [x] Shared `FilmCatalogMetadata` with `compact` and `full` variants on film detail and movie cards.
- [x] Passport line shows colored KP/IMDb ratings, duration, age limit, trailer chip or empty state.
- [x] Providers and similar titles collapse on full film pages; compact cards hide similar scroll.
- [x] Similar titles link to `/films/:id` when matched in catalog, otherwise to search with prefilled query.
- [x] Backend resolves TMDB recommendations to structured `FilmRecommendationItem` list.
- [x] Frontend unit tests for display helpers; backend unit tests for recommendation resolver.
