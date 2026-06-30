# Backend Parallel Test Execution and Coverage Reporting

## Metadata
- Feature slug: backend-parallel-test-coverage
- Title: Backend Parallel Test Execution and Coverage Reporting
- Status: planned
- Author: r.makkhmudov
- Created at: 2026-06-30
- Priority: high
- Target area: backend

## Problem
- The backend test suite still relies on a mostly serial execution model, which leaves runtime improvements on the table.
- CI does not surface coverage artifacts and a short coverage summary as clearly as it could.
- Parallel execution must remain safe with PostgreSQL-backed tests and shared bootstrap state.

## Scope
- Make backend pytest runs xdist-safe by isolating each worker with its own PostgreSQL schema.
- Ensure worker schema selection happens early enough for database and app bootstrap code to use it consistently.
- Publish coverage artifacts in CI, including `coverage.xml` and HTML coverage output.
- Add a short coverage summary to the GitHub Actions job summary.
- Keep local developer workflows usable for both full-suite and targeted backend test runs.
- Add tests covering bootstrap behavior, worker schema naming, and cleanup/isolation behavior.

## Functional Requirements
- [ ] Backend tests can run in parallel without cross-worker database collisions.
- [ ] Each xdist worker gets a deterministic, isolated PostgreSQL schema before backend modules bind to database settings.
- [ ] The shared backend test bootstrap still resets global in-memory test state safely.
- [ ] CI uploads coverage artifacts and writes a concise coverage summary to the GitHub Actions step summary.
- [ ] Local backend test commands remain straightforward for both full runs and focused debugging.
- [ ] Backend tests explicitly cover bootstrap timing, schema naming, and cleanup behavior.

## Acceptance Criteria
- [ ] Running the backend suite with xdist does not cause schema or table collisions between workers.
- [ ] The CI workflow produces coverage artifacts that can be downloaded after a run.
- [ ] The CI workflow shows a short coverage summary directly in the GitHub Actions UI.
- [ ] Existing backend tests remain green under the new execution model.
- [ ] New or updated tests verify the bootstrap and schema isolation path.

## Constraints
- Technical constraints:
- Must be safe for `pytest-xdist`.
- Must work with one PostgreSQL service shared across workers in CI.
- Must preserve existing bootstrap ordering requirements.
- Must keep the test environment deterministic and cleanup-safe.
- Product/design constraints:
- Keep the change focused on test execution optimization and coverage reporting.
- Prefer low-friction local usability over a CI-only optimization.

## References
- Related issue/ticket: legacy plan `.cursor/plans/backend-parallel-coverage_c6031a20.plan.md`
- Related files/modules:
  - `Makefile`
  - `backend/pyproject.toml`
  - `backend/src/core/database.py`
  - `backend/src/tests/conftest.py`
  - `backend/src/tests/support/db_setup.py`
  - `backend/src/tests/support/plugins.py`
  - `backend/src/tests/support/xdist_bootstrap.py`
  - `.github/workflows/ci-backend.yml`
