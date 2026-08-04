# Plan: app-hardening-pass

1. Audit hot paths (global feed, auth, SSE, JWT).
2. Fix JWT missing `exp` (Bearer tokens lived forever in sessionStorage).
3. Validate stored Bearer via `/api/me` before `ready` state.
4. Add DB indexes for global feed sort columns (`user_card.updated_at`, `feed_post.created_at`).
5. Release SSE `ReadableStream` reader on abort in `globalFeedSse.ts`.
6. Add pytest for JWT expiry; run Docker-backed verification.
7. Document findings (fixed vs deferred) in result + docs.
