# Action log — global feed sort indexes migration

- **Timestamp:** 2026-07-23T16:24:00Z
- **Feature slug:** app-hardening-pass
- **Action type:** test
- **Summary:** Applied pending Alembic migration `b3c4d5e6f789_global_feed_sort_indexes.py` (global feed sort indexes on `user_card.updated_at` and `feed_post.created_at`).
- **Files:** `backend/src/migrations/versions/b3c4d5e6f789_global_feed_sort_indexes.py`
- **Verification:**
  - Before: `a2b3c4d5e678`
  - After: `b3c4d5e6f789 (head)`
  - Command: `docker exec -w /opt/app filmony-backend alembic upgrade head` — exit 0
  - Note: `make migrate` exit 1 in non-TTY agent shell (`docker exec -it` stdin attach error); used non-interactive equivalent per `.cursor/tech.md`
