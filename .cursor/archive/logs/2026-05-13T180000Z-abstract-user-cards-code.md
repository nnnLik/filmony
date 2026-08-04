# 2026-05-13T180000Z — abstract-user-cards — code

- **Timestamp:** 2026-05-13T180000Z  
- **Feature slug:** abstract-user-cards  
- **Action type:** code  

## Summary

Universal user cards: extended `CardCreateRequest` with three mutually exclusive modes (film + kinopoisk, `catalog_item_id`, manual `display_title`); `CreateMovieCardService` sets `catalog_item_id` for film creates when a catalog row exists, enforces partial unique conflicts, and populates display fields. Read paths (`GetMovieCardDetailsService`, feed hydration, profile card lists, inline picker, inline `⟦c⟧` resolution, feed-post referenced cards, following-ratings) support nullable `film_id` and expose `catalog_item_id` plus display fields while keeping deprecated `film_*` populated when a `Film` row exists or mirroring manual titles.

## Files

- `backend/src/api/cards/schemas.py`
- `backend/src/api/cards/routes.py`
- `backend/src/api/feed/routes.py`
- `backend/src/api/profile/schemas.py`
- `backend/src/services/cards/create_movie_card.py`
- `backend/src/services/cards/get_movie_card_details.py`
- `backend/src/services/cards/list_movie_card_feed.py`
- `backend/src/services/cards/list_following_ratings_for_movie_card.py`
- `backend/src/services/cards/list_my_movie_cards_for_inline_picker.py`
- `backend/src/services/cards/inline_movie_card_ref_tokens.py`
- `backend/src/services/profile/list_user_movie_cards.py`
- `backend/src/tests/api/test_cards_routes.py`

## Verification

- `docker compose -f docker-compose.yml exec -w /opt/app backend pytest src/tests/api/test_cards_routes.py src/tests/api/test_profile_routes.py -q`
- `docker compose -f docker-compose.yml exec -w /opt/app backend ruff check --fix src/services/cards/create_movie_card.py`

## Links

- Progress: `.cursor/active/abstract-user-cards/progress.md`
