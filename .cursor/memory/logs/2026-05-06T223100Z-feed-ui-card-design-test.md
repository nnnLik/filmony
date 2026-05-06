- Timestamp: 2026-05-06 22:31 UTC
- Feature slug: `feed-ui-card-design`
- Action type: `test`

## Summary
Добавлены pytest-кейсы для ленты: `test_movie_card_feed_requires_auth`, `test_movie_card_feed_includes_comments_count_and_preview`, `test_movie_card_feed_cursor_pagination` в `backend/src/tests/api/test_cards_routes.py`.

## Files
- `backend/src/tests/api/test_cards_routes.py`

## Verification
- Ожидаемый запуск в контейнере `filmony-backend`:  
  `make backend-test-one target='src/tests/api/test_cards_routes.py::test_movie_card_feed_requires_auth src/tests/api/test_cards_routes.py::test_movie_card_feed_includes_comments_count_and_preview src/tests/api/test_cards_routes.py::test_movie_card_feed_cursor_pagination'`  
  либо `make backend-test`.
