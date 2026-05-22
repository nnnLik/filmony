Timestamp: 2026-05-22T153700Z
Feature slug: `rawg-card-linking`
Action type: `test`

## Summary

Added API regression coverage for following-ratings with shared RAWG `catalog_item_id` (subscription list sorting and `viewer_rating`).

## Files

- `backend/src/tests/api/test_following_ratings_for_movie_card.py`

## Verification

`docker exec -w /opt/app filmony-backend pytest src/tests/api/test_following_ratings_for_movie_card.py -v`
