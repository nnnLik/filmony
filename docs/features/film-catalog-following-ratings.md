# Following ratings on film & catalog pages

«Друзья оценили» on title pages: up to 5 following users who rated the same title, plus viewer row when applicable.

## API
- `GET /api/films/{film_id}/following-ratings`
- `GET /api/catalog/items/{catalog_item_id}/following-ratings`
- `GET /api/cards/{card_id}/following-ratings` (unchanged; delegates to title service)

## Frontend
- `FollowingRatingsPanel` on FilmDetailPage, CatalogDetailPage (above community ratings)
- Hidden when not authenticated
