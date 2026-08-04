# Film & catalog following ratings

## Scope
Show «Друзья оценили» on `/films/:id` and `/catalog/:id` (auth required).

## Acceptance
- `ListFollowingRatingsForTitleService` with `film_id` OR `catalog_item_id`
- `GET /api/films/{id}/following-ratings`, `GET /api/catalog/items/{id}/following-ratings`
- Card endpoint delegates to title service
- `FollowingRatingsPanel` on FilmDetailPage, CatalogDetailPage, MovieCardDetailPage
- pytest: `test_following_ratings_for_title.py`
