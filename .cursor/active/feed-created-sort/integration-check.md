# feed-created-sort integration check

**Verdict: NEEDS_FIX**

## Checks

- **Indexes (model ↔ migration)** — PASS  
  `ix_user_card_completed_at_id` (`completed_at`, `id` DESC; `is_planned IS FALSE AND completed_at IS NOT NULL`) and `ix_user_card_user_id_completed_at_id` (`user_id`, `completed_at`, `id` DESC; `is_planned IS FALSE`) match in `backend/src/models/user_card.py` and `backend/src/migrations/versions/j8k9l0m1n234_user_card_completed_at_feed_indexes.py`. `down_revision` is `i7j8k9l0m123`.

- **Feed/profile sorts** — PASS  
  Global card branch: `completed_at`, exclude planned and null `completed_at` (`list_global_feed.py`). Personal feed `_ordered_cards` / `_build_affinity_stream`: same filters, `ORDER BY completed_at DESC, id DESC`. Profile `sort=recent`: `desc(completed_at).nulls_last()`, `rec1.` cursor. Posts stay on `created_at`.

- **Expected behavior coverage** — PASS  
  Tests cover PATCH rating/favorite not bumping, later→rated surfacing, planned excluded from global cards, `rec1.` pagination. Personal feed has PATCH-does-not-promote (`test_feed_rating_patch_does_not_promote_older_card`).

- **Docstring vs code** — PASS  
  `list_global_feed.py` module/class docstrings match: cards by `completed_at`, planned/null excluded, PATCH does not move the feed.

- **Unused imports (`cast`, `sa`)** — PASS  
  Migration uses `sa.text(...)`. `cast` in `list_user_cards.py` is a local import used for genre JSONB. `and_` is imported and used in `list_global_feed.py`. (Repo ruff ignores `F401`, so CI would not catch a future unused import.)

- **Missing `and_` import** — PASS  
  `from sqlalchemy import Integer, String, and_, or_, select, union_all` in `list_global_feed.py`; used in the keyset `where`.

- **Ruff E501 on `card_branch` line** — PASS  
  `card_branch` is already split; `.select_from(UserCard).where(*card_filters)` is well under `line-length = 100`. `E501` is ignored in `backend/pyproject.toml` anyway.

- **Test names / helpers still referencing `updated_at`** — FAIL  
  `backend/src/tests/integration/api/test_global_feed_routes.py`: helper `_card_updated_at_before_post` (lines 41–48) still assigns `card.updated_at`. Chronology test `test_global_feed_cards_and_posts_chronology` calls it (line 84). Sort is `completed_at` vs post `created_at`; mutating `updated_at` is a no-op. Rename helper and set `card.completed_at = post.created_at - timedelta(...)`. Test function names themselves were already rewritten.

- **`datetime.min` timestamp / `rec1` null sentinel** — FAIL  
  `backend/src/services/profile/list_user_cards.py`: `_RECENT_NULL_CURSOR_DT = dt.datetime.min.replace(tzinfo=dt.UTC)` then `_encode_recent_cursor` does `int(completed_at.timestamp() * 1_000_000)`. Year-0001 µs overflow float64 (mantissa 2^53), so decode may not equal the sentinel and `cursor_dt == _RECENT_NULL_CURSOR_DT` can miss; on Windows `.timestamp()` can raise `OSError`. Fix: dedicated null token (e.g. `rec1.null.{id}`) or a round-trippable epoch sentinel. Hits only profile recent pagination over NULL `completed_at` (post-backfill rare); feeds exclude nulls.

## Summary bullets

- Indexes, sorts, planned exclusion, PATCH/later→rated tests, `rec1.` prefix, migration revision: consistent.
- Fix leftover `_card_updated_at_before_post` (set `completed_at`, not `updated_at`).
- Fix `_RECENT_NULL_CURSOR_DT` / `datetime.min` encoding before relying on null-page keyset.
