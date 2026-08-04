# Backend unit / integration test split

Completed on 2026-08-04.

Backend pytest is split by directory:

- `backend/src/tests/unit/` contains Postgres-free tests. Run `make backend-test-unit`.
- `backend/src/tests/integration/` contains database and ASGI coverage. Run `make backend-test-integration`.
- `make backend-test` runs both suites sequentially.

The unit suite rejects `prepare_db` and `async_client`; integration tests use per-xdist-worker schemas. CI runs `backend-lint`, `backend-unit`, and `backend-integration` in parallel, with coverage produced by integration only.

Verification: [CI run 30903120160](https://github.com/nnnLik/filmony/actions/runs/30903120160) passed all three jobs.
