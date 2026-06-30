---
name: backend-parallel-coverage
overview: Optimize backend test execution and CI by making pytest-xdist-safe test runs the default, isolating each worker with its own PostgreSQL schema, and publishing coverage data in GitHub Actions.
todos:
  - id: audit-current-test-flow
    content: Confirm the exact import order and database setup path that currently makes the backend test suite single-worker only.
    status: completed
  - id: add-worker-isolation
    content: Ensure every xdist worker gets a dedicated schema before app/database modules connect so shared tables never collide.
    status: completed
  - id: wire-coverage
    content: Add pytest-cov output and surface coverage artifacts plus a short summary in GitHub Actions.
    status: completed
  - id: update-ci-and-make
    content: Update the backend test command and CI workflow to use the parallel coverage flow by default.
    status: completed
  - id: verify-tests
    content: Extend backend tests for the bootstrap, schema naming, and cleanup behavior, then confirm the suite stays green.
    status: completed
isProject: false
---

# Backend Test and CI Optimization

## Goal
Make backend tests safe and fast to run in parallel while improving CI visibility with coverage reports and downloadable artifacts.

## Why this matters
The backend suite currently relies on a shared test database and a serial execution model. That is reliable, but it leaves test runtime on the table and makes CI less informative than it could be.

## Current state
- `backend/src/tests/conftest.py` bootstraps a shared database and resets it around each test.
- `backend/src/tests/support/db_setup.py` creates and drops tables against the active engine.
- `backend/src/tests/support/plugins.py` already initializes test environment state before the app imports.
- `backend/src/tests/support/xdist_bootstrap.py` contains the worker-schema naming logic needed for isolated parallel workers.
- `Makefile` still runs `pytest` serially by default.
- `.github/workflows/ci-backend.yml` runs backend tests without coverage artifacts or a coverage summary.

## Implementation plan
1. Confirm the current pytest bootstrap sequence and the exact point where worker-specific schema selection must happen.
2. Keep the xdist schema bootstrap deterministic:
   - derive a schema name from `PYTEST_XDIST_WORKER`
   - set `PYTEST_DB_SCHEMA` before backend modules read database settings
   - reuse one PostgreSQL service in CI instead of provisioning per-worker databases
3. Update test DB helpers so `create_all_tables` and `drop_all_tables` operate inside the worker schema and clean up safely after each test.
4. Preserve the existing test reset behavior for the global feed broker and any other shared in-memory state.
5. Update backend test commands in `Makefile`:
   - default backend test target should use parallel execution and coverage
   - targeted local debugging should still work with a single-test command
6. Update `.github/workflows/ci-backend.yml`:
   - run the new backend test command
   - upload `coverage.xml` and `htmlcov/` as artifacts
   - write a concise coverage summary to `GITHUB_STEP_SUMMARY`
7. Add or adjust backend tests so the new worker schema selection and bootstrap path are explicitly covered.

## Files likely to change
- [Makefile](Makefile)
- [backend/pyproject.toml](backend/pyproject.toml)
- [backend/src/core/database.py](backend/src/core/database.py)
- [backend/src/tests/conftest.py](backend/src/tests/conftest.py)
- [backend/src/tests/support/db_setup.py](backend/src/tests/support/db_setup.py)
- [backend/src/tests/support/plugins.py](backend/src/tests/support/plugins.py)
- [backend/src/tests/support/xdist_bootstrap.py](backend/src/tests/support/xdist_bootstrap.py)
- [.github/workflows/ci-backend.yml](.github/workflows/ci-backend.yml)
- [backend/src/tests/**](backend/src/tests/)

## Success criteria
- Backend tests can run in parallel without cross-worker database collisions.
- Coverage is generated during CI and visible in the GitHub Actions run summary, with downloadable artifacts.
- The backend test command remains easy to use locally for both full-suite and targeted runs.
- Existing backend tests remain green under the new execution mode.
