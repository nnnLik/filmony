# App Hardening Pass

## Scope
Evidence-based fixes for security, query performance, and frontend resource leaks on hot paths.

## Acceptance criteria
- Top 3–7 proven issues fixed with verification
- JWT sessions expire; stale Bearer tokens re-auth
- Global feed sort queries use supporting indexes
- SSE consumer releases fetch reader on abort
- Delivery artifacts + tests for backend security/query fixes
