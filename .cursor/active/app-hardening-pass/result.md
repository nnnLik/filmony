# Result: app-hardening-pass

Status: **completed**

## Findings (fixed)

| Issue | Impact | Fix | Verification |
|-------|--------|-----|--------------|
| Session JWT had no `exp` | Bearer in `sessionStorage` never expired server-side | `IssueSessionJwtService` sets `iat`+`exp` from `SESSION_MAX_AGE_SECONDS` | `backend/src/tests/auth/test_session_jwt.py` |
| AuthProvider marked `ready` without validating stored Bearer | Stale token UI; silent API 401s | Probe `/api/me` with Bearer; fall through to re-auth on failure | Manual + existing auth tests |
| Global feed sorts by `user_card.updated_at` / `feed_post.created_at` without matching indexes | Seq scans on hot pagination path | Migration `b3c4d5e6f789` + model indexes | Alembic upgrade + query plan (follow-up EXPLAIN) |
| SSE reader not cancelled on abort | Leaked stream handles on feed navigation | `reader.cancel()` in `finally` in `globalFeedSse.ts` | Code review |

## Findings (deferred)

| Issue | Why deferred |
|-------|--------------|
| Legacy JWTs without `exp` still accepted until re-login | Breaking all sessions requires coordinated rollout; new tokens carry `exp` |
| OpenAPI `limit` params without `le=` on some routes | Services already cap via `min(limit, 50)` — low risk, API contract unchanged |
| Cookie-only sessions without Bearer probe on every mount | Cookie path already probes `/api/me/profile`; acceptable |
| N+1 suspicion in reaction hydration | Batch loaders already used in `list_user_card_feed.py`; no proven regression |

## Changed files

- `backend/src/services/auth/issue_session_jwt.py`
- `backend/src/tests/auth/test_session_jwt.py`
- `backend/src/migrations/versions/b3c4d5e6f789_global_feed_sort_indexes.py`
- `backend/src/models/user_card.py`
- `backend/src/models/feed_post.py`
- `frontend/src/lib/globalFeedSse.ts`
- `frontend/src/auth/AuthProvider.tsx`

## Residual risks

- Pre-existing JWTs without `exp` remain valid until users re-authenticate.
- Index benefit depends on table size; monitor slow queries on `/api/feed/global`.
