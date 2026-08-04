# Franchise catalog pages

## Scope
Community franchise hub mirroring director catalog.

## Acceptance
- `GET /api/franchises/{key}`, `/films`; label from root Kinopoisk id
- `franchise_key` / label on film DTOs; FranchiseChip + FranchiseDetailPage
- Index migration `ix_film_franchise_key`
- Optional `GET /api/users/{id}/rated-franchises`
- pytest: `test_franchises_routes.py`
