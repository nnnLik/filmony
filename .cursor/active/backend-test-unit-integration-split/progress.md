# backend-test-unit-integration-split — progress

**Status:** completed  
**Started:** 2026-08-04T131500Z

## 2026-08-04 — Planning

- Read approved design spec (`docs/superpowers/specs/2026-08-04-backend-unit-integration-test-split-design.md`).
- Created feature spec, active plan (migration steps 2–12), superpowers implementation plan.
- Registered slug in `.cursor/HOT.md` as `in_progress`.
- No test file moves or backend code changes yet.

**Next:** Step 2 — create `unit/` and `integration/` directory skeleton.

## 2026-08-04 — Migration and runner wiring (partial)

### File moves

- Moved all test modules into `tests/unit/` and `tests/integration/` (mirror domain folders).
- **Counts:** 26 unit test modules, 61 integration test modules (87 total).
- Removed legacy flat folders at `tests/` root (former top-level `api/`, etc.).
- Shared helpers remain in `tests/support/`; auth signing helper in `tests/auth/telegram_init_data.py`.

### Guards and bootstrap

- Added `tests/unit/conftest.py` collection guard — rejects `prepare_db` / `async_client` under `unit/`.
- Updated `tests/support/plugins.py` with `_collection_needs_db()` — unit-only runs skip Postgres schema bootstrap.

### Pyproject

- `testpaths` → `["src/tests/unit", "src/tests/integration"]` in `backend/pyproject.toml`.

### Makefile / CI — done

- Root `Makefile`: added `backend-test-unit` (`--no-cov -n auto --dist=loadscope`), `backend-test-integration`, and sequential `backend-test`; `backend-test-one` requires `unit/` or `integration/` path prefix.
- `.github/workflows/ci-backend.yml`: split into parallel `backend-unit` (no Postgres, no coverage) and `backend-integration` (Postgres + coverage + Codecov); `backend-lint` unchanged.

### Docs (this session)

- Updated `backend/src/tests/README.md`, `.cursor/tech.md`, skill/rule/reference — post-split layout and make/CI contract; removed “until split lands” hedging.

## 2026-08-04 — Verification (in progress)

- Local Docker: run `make backend-test-unit` (no Postgres), `make backend-test-integration`, and `make backend-test` (full suite).
- CI: confirm `backend-lint`, `backend-unit`, and `backend-integration` green on PR.

**Next:** Finish local/CI verification, then closeout (`result.md`, feature doc, HOT, action-log).

## 2026-08-04 — Integration slowness investigation

Measured in Docker against `homelab-postgres` (485 tests collected; 8 import errors from stale `tests.api` imports).

- **Dominant cost:** `prepare_db` runs `reset_worker_schema()` + `create_all_tables()` before each test and `reset_worker_schema()` twice + `dispose_engine()` twice in teardown (`plugins.py:60-70`, `db_setup.py:36-45`). Per-test setup ~0.25–0.69s, teardown ~0.08–0.10s on trivial API tests.
- **Coverage:** default `addopts` applies `--cov=src --cov-branch` to integration (unit uses `--no-cov`). Two-route file: 0.67s vs 8.65s (~13×). `test_cards_routes.py` (87 tests): 35s no-cov vs 68s with cov+xdist.
- **xdist loadscope:** large modules (`test_cards_routes` 87, `test_feed_posts_routes` 45) run sequentially on one worker despite `-n auto`.
- **Full-suite estimate:** ~370 runnable tests sequential no-cov ≈ **3.2 min** fixture+test baseline; with default cov+xdist expect **~5–10 min** locally (remote Postgres); CI localhost likely faster.
- **Follow-ups (speed):** session-scoped DB reset or TRUNCATE vs DROP SCHEMA×2; `--no-cov` for local integration; consider `--dist=loadfile`; local Postgres service for dev.

## 2026-08-04 — Closeout

- Fixed all move-related imports and made `integration/` a package.
- CI unit job now installs production runtime dependencies and provides required placeholder settings; integration job has a Redis service for Celery-backed tests.
- Stabilized test database isolation with per-worker schemas, `NullPool` in test mode, and atomic schema resets; CI integration completed successfully.
- CI run `30903120160`: `backend-lint`, `backend-unit`, and `backend-integration` all green.
- Local unit verification passed: **148 passed in 3.54s**. The local rebuilt Docker dev image loses production dependencies when `uv run` resolves only the dev group; CI supplied authoritative full integration evidence.
