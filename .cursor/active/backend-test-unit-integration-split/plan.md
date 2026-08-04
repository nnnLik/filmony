# backend-test-unit-integration-split — active plan

**Status:** in_progress  
**Started:** 2026-08-04  
**Spec:** `docs/superpowers/specs/2026-08-04-backend-unit-integration-test-split-design.md`  
**Implementation plan:** `docs/superpowers/plans/2026-08-04-backend-test-unit-integration-split.md`

Single PR — big-bang file moves plus runner/CI wiring. Branch e.g. `chore/backend-test-unit-integration-split`.

## Step 2 — Create directory skeleton

- [ ] Create `backend/src/tests/unit/` with mirrored subfolders (`lib/`, `providers/`, `services/`, `auth/`, …)
- [ ] Create `backend/src/tests/integration/` with mirrored subfolders (`api/`, `services/`, `migrations/`, `scripts/`, `tasks/`, `models/`, …)
- [ ] Leave `support/`, root `conftest.py` in place

## Step 3 — Classify and move test modules

- [ ] All `api/**` → `integration/api/**`
- [ ] Each `services/**` file → `unit/services/**` or `integration/services/**` per fixture usage (`prepare_db`, `async_client`, real DAO)
- [ ] `providers/`, `lib/`, non-DB `auth/` → mostly `unit/`
- [ ] `migrations/`, `scripts/`, DB-heavy `tasks/`, `models/` → `integration/`
- [ ] Use `git mv` for every module; keep `from tests.support…` imports unchanged
- [ ] Remove legacy top-level domain folders after all files moved
- [ ] PR description: classification table (source → destination counts by folder)

## Step 4 — Unit fixture guard

- [ ] Add `backend/src/tests/unit/conftest.py` with `pytest_collection_modifyitems` guard
- [ ] Fail collection if any test under `unit/` requests `prepare_db` or `async_client`

## Step 5 — Gate session bootstrap

- [ ] Update `tests/support/plugins.py`: gate `pytest_sessionstart` / `ensure_schema_exists()` to integration collection only
- [ ] Confirm unit-only runs do not open a DB connection

## Step 6 — Pytest paths

- [ ] Update `backend/pyproject.toml` `testpaths` to `["src/tests/unit", "src/tests/integration"]`

## Step 7 — Makefile targets

- [ ] Add `backend-test-unit` (`--no-cov -n auto --dist=loadscope`)
- [ ] Add `backend-test-integration` (inherits `addopts` cov)
- [ ] Change `backend-test` to run unit then integration sequentially
- [ ] Document `backend-test-one` path must include `unit/` or `integration/` prefix

## Step 8 — CI split

- [ ] Update `.github/workflows/ci-backend.yml`: new `backend-unit` job (no Postgres, no coverage)
- [ ] Rename/split current `backend-test` → `backend-integration` (Postgres + coverage + Codecov)
- [ ] Keep `backend-lint` unchanged; all three jobs parallel (no `needs`)

## Step 9 — Developer docs

- [ ] Update `backend/src/tests/README.md`: layout, classification rules, make targets, CI jobs

## Step 10 — Local verification (Docker)

- [ ] `make backend-test-unit` — passes without Postgres
- [ ] `make backend-test-integration` — passes with Postgres
- [ ] `make backend-test` — full suite green

## Step 11 — CI verification

- [ ] PR: `backend-lint`, `backend-unit`, `backend-integration` all green
- [ ] Codecov fed from integration artifacts only

## Step 12 — Agent docs (same PR or immediate follow-up)

- [ ] Update `.cursor/tech.md` with new `make backend-test-one` path prefixes
- [ ] Align `feature-delivery-workflow` references if needed

## Closeout

- [ ] Write `result.md` and `docs/features/backend-test-unit-integration-split.md`
- [ ] Update HOT (move slug to `recent_completed`)
- [ ] Append milestone/closeout action-log fragment
