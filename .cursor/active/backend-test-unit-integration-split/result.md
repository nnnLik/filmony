# backend-test-unit-integration-split — result

**Status:** completed  
**Closed:** 2026-08-04

## Delivered

- Partitioned backend tests into `unit/` and `integration/` trees with a fixture guard and Postgres-free unit bootstrap.
- Added Makefile and CI jobs for unit, integration, and complete test runs.
- Repaired moved-test imports, CI runtime settings, Redis-backed Celery tests, worker-schema isolation, and async database connection handling.

## Verification

- Local: `make backend-test-unit` — **148 passed in 3.54s**.
- CI: [run 30903120160](https://github.com/nnnLik/filmony/actions/runs/30903120160) — `backend-lint`, `backend-unit`, and `backend-integration` all passed.
- CI integration includes coverage upload and completed in about 6m29s.

## Follow-ups

- The integration suite still recreates schemas per test. Evaluate transactional cleanup or truncation separately before changing its isolation model.
- The Docker dev image currently resolves `uv run` with only the dev group after a rebuild; preserve prod dependencies in that image as a separate environment fix.
