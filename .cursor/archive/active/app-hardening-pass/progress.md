# Progress: app-hardening-pass

Status: **completed**

- Audited global feed, auth JWT, SSE consumer, AuthProvider bootstrap.
- Fixed JWT `exp`/`iat`, AuthProvider Bearer validation, SSE reader cleanup, global feed indexes.
- Added `backend/src/tests/auth/test_session_jwt.py`.
- Pending verification: `make backend-test-one target=src/tests/auth/` + frontend lint/build.
- Verified: `make backend-test-one target=src/tests/auth/test_session_jwt.py` — 3 passed.
- Frontend lint on touched files: clean. Full `npm run lint` fails on pre-existing `FeedPostDetailPage.tsx` unused vars (out of scope).
