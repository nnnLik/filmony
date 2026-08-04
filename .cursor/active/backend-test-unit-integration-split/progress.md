# backend-test-unit-integration-split — progress

**Status:** in_progress  
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
