# App hardening pass

Security and performance fixes on authentication and global feed hot paths.

## What changed

### Session JWT expiration
Bearer tokens returned from `POST /api/auth/telegram` now include `iat` and `exp` aligned with `SESSION_MAX_AGE_SECONDS`. Previously tokens lacked `exp`, so copies in `sessionStorage` stayed valid indefinitely even after cookie expiry.

### Auth bootstrap validation
`AuthProvider` no longer enters `ready` solely because a Bearer token exists. It probes `GET /api/me` first and re-runs Telegram auth when the token is rejected.

### Global feed query indexes
Added btree indexes for sort keys used by `ListGlobalFeedService`:
- `ix_user_card_updated_at_id` on `(updated_at DESC, id DESC)`
- `ix_feed_post_created_at_id` on `(created_at DESC, id DESC)`

### SSE resource cleanup
`consumeGlobalFeedHeadSse` cancels the fetch `ReadableStream` reader in a `finally` block when the feed page unmounts or the abort signal fires.

## Verification

```bash
make backend-test-one target=src/tests/auth/test_session_jwt.py
make backend-test-one target=src/tests/auth/test_telegram.py
cd frontend && npm run lint && npm run build
```

## Follow-ups

- Optionally reject JWTs missing `exp` after a grace period.
- Add `le=` caps on OpenAPI `limit` query params for documentation parity.
