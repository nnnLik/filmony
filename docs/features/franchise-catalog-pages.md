# Franchise catalog pages

Community franchise hub at `/franchises/:franchiseKey` (URL-encode `kp_franchise:301`).

## API
- `GET /api/franchises/{key}` — summary + label from root Kinopoisk film title
- `GET /api/franchises/{key}/films` — rated films, cursor pagination
- `GET /api/users/{id}/rated-franchises` — profile filter dropdown

## UI
- `FranchiseChip` on film/card/feed surfaces; marathon chips navigate to franchise page
