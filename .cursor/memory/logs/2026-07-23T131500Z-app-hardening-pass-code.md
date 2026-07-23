# Action log

- **Timestamp:** 2026-07-23T13:15:00Z
- **Feature slug:** app-hardening-pass
- **Action type:** code
- **Summary:** JWT exp claims, global feed sort indexes, SSE reader cleanup, AuthProvider Bearer validation.
- **Files:**
  - `backend/src/services/auth/issue_session_jwt.py`
  - `backend/src/tests/auth/test_session_jwt.py`
  - `backend/src/migrations/versions/b3c4d5e6f789_global_feed_sort_indexes.py`
  - `backend/src/models/user_card.py`
  - `backend/src/models/feed_post.py`
  - `frontend/src/lib/globalFeedSse.ts`
  - `frontend/src/auth/AuthProvider.tsx`
- **Verification:** `make backend-test-one target=src/tests/auth/test_session_jwt.py`
