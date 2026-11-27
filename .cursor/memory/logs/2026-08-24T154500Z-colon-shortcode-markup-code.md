# 2026-08-24T154500Z-colon-shortcode-markup-code

- Timestamp: 2026-08-24T154500Z
- Feature slug: `colon-shortcode-markup`
- Action type: `code`
- Summary: Catalog DTO/schema/mapper expose `shortcode`. Comment and feed-post validators canonicalize legacy `⟦r{id}⟧` / `[[r{id}]]` via `rewrite_reaction_tokens`, re-check max length after rewrite, keep unknown `:foo:` literal, and still 422 unknown legacy ids.

## Files
- `backend/src/api/reactions/schemas.py`
- `backend/src/api/reactions/routes.py`
- `backend/src/services/reactions/list_reaction_catalog.py`
- `backend/src/services/cards/comment_reaction_tokens.py`
- `backend/src/services/feed_posts/validate_feed_post_body.py`
- `backend/src/models/reaction_type.py`
- `backend/src/migrations/versions/k1l2m3n4o567_reaction_type_shortcode.py`
- `backend/src/tests/unit/services/cards/test_comment_reaction_tokens.py`
- `backend/src/tests/unit/services/feed_posts/test_validate_feed_post_body.py`
- `backend/src/tests/unit/api/reactions/test_catalog_schema.py`
- `backend/src/tests/integration/api/test_reactions_routes.py`
- `backend/src/tests/integration/api/test_cards_routes.py`
- `backend/src/tests/integration/api/test_feed_posts_routes.py`

## Verification
- `ruff check` + `ruff format --check` on touched backend files: passed (host venv; Docker unavailable)
- `pytest -n0 --no-cov src/tests/unit/api/reactions/test_catalog_schema.py src/tests/unit/services/cards/test_comment_reaction_tokens.py src/tests/unit/services/feed_posts/test_validate_feed_post_body.py`: 14 passed
- `pytest -n0 --no-cov src/tests/unit/services/test_reaction_shortcodes.py` (with the validator files earlier): shortcode helpers included in the 25-passed run
- Integration catalog/comment/feed HTTP tests not run here (no Docker/Postgres)
