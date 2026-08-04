Timestamp: 2026-05-14T120000Z
Feature slug: abstract-user-cards
Action type: code

Summary: Renamed ORM domain types from `movie_card*` models to general user-card models (`UserCard`, `CardComment`, `CardTag`) with legacy `__tablename__`/column mappings; aliased feed post ORM attribute `referenced_card_id` ↔ DB `referenced_movie_card_id`; generalized `ReactionTargetKind` enum members while keeping stored `'movie_card*'` strings; introduced `CatalogProvider(StrEnum)` for `CatalogItem.provider` with string-backed SA `Enum`; updated services/API/tests accordingly.

Files:
- `backend/src/models/user_card.py` (new; table `movie_card`)
- `backend/src/models/card_comment.py` (new; table `movie_card_comment`; `card_id` → column `movie_card_id`)
- `backend/src/models/card_tag.py` (new; table `movie_card_tag`; `card_id` → column `movie_card_id`)
- `backend/src/models/card_enums.py` (new)
- `backend/src/models/catalog_item.py`
- `backend/src/models/feed_post.py`
- `backend/src/models/reaction_target_kind.py`
- `backend/src/models/__init__.py`
- Removed: `backend/src/models/movie_card.py`, `movie_card_comment.py`, `movie_card_tag.py`, `movie_card_enums.py`
- `backend/src/api/catalog/schemas.py`
- `backend/src/api/feed_posts/schemas.py`
- `backend/src/services/catalog/resolve_catalog_item_service.py`
- Plus import/ORM attribute updates across `backend/src/services/**`, `backend/src/api/**`, `backend/src/tests/**`

Verification: `make backend-test` (217 passed, Docker `backend` container).

Links: `.cursor/active/abstract-user-cards/progress.md`
