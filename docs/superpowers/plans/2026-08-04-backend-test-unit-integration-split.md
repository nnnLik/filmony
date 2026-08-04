# Backend Test Unit / Integration Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> Spec source of truth: [docs/superpowers/specs/2026-08-04-backend-unit-integration-test-split-design.md](docs/superpowers/specs/2026-08-04-backend-unit-integration-test-split-design.md) · Feature: [.cursor/features/backend-test-unit-integration-split/feature.md](.cursor/features/backend-test-unit-integration-split/feature.md)

**Goal:** Partition backend pytest into `tests/unit/` and `tests/integration/` with directory-based classification, Postgres-free unit runs (`make backend-test-unit`), split CI jobs, and preserved full-suite semantics via `make backend-test`.

**Architecture:** Directories are the source of truth for test type. Shared fixtures live in `tests/support/` (sibling to both trees). A light collection guard in `unit/conftest.py` blocks forbidden DB/ASGI fixtures. `pytest_sessionstart` schema bootstrap runs only when integration tests are collected. Makefile and CI expose separate unit and integration targets; integration job remains authoritative for coverage/Codecov.

**Tech Stack:** pytest + pytest-asyncio + pytest-xdist, Docker backend container, GitHub Actions (`ci-backend.yml`), root Makefile, `backend/pyproject.toml`.

## Global Constraints

- **Single big-bang PR** — no long-lived dual layout or per-file opt-in markers.
- **No production code changes** — test module imports stay `from tests.support…`.
- **No v1 mock rewrites** — DB-backed service tests stay integration; only classify and move.
- **Directories decide type** — not `@pytest.mark.integration`.
- **`support/` stays shared** — never under `unit/` or `integration/`.
- **Coverage v1:** integration job only; unit job runs with `--no-cov`.
- **Docker-first:** run pytest/ruff inside `filmony-backend` container per `.cursor/tech.md`.
- Delivery artifacts: `.cursor/active/backend-test-unit-integration-split/{plan,progress,result}.md`, `docs/features/backend-test-unit-integration-split.md`.

---

## Task 1 — Directory skeleton

- [ ] Create `backend/src/tests/unit/` with mirrored domain subfolders
- [ ] Create `backend/src/tests/integration/` with mirrored domain subfolders
- [ ] Confirm `support/`, root `conftest.py` unchanged

**Verify:** Empty tree structure exists; no legacy folders removed yet.

## Task 2 — Classify and `git mv` test modules

- [ ] Move all `api/**` → `integration/api/**`
- [ ] Classify each `services/**` file by fixtures (unit vs integration)
- [ ] Move `providers/`, `lib/`, non-DB `auth/` → mostly `unit/`
- [ ] Move `migrations/`, `scripts/`, DB-heavy `tasks/`, `models/` → `integration/`
- [ ] Remove empty legacy top-level domain folders
- [ ] Add PR classification table (source → destination counts)

**Verify:** Every test module lives under `unit/` or `integration/`; imports unchanged; `git mv` history preserved.

## Task 3 — Unit conftest guard

- [ ] Add `backend/src/tests/unit/conftest.py` with `_FORBIDDEN_IN_UNIT` and `pytest_collection_modifyitems`
- [ ] Reject `prepare_db` and `async_client` under `unit/`

**Verify:** Misplaced fixture usage fails at collection with clear `UsageError`.

## Task 4 — Gate `pytest_sessionstart`

- [ ] Update `tests/support/plugins.py` to skip `ensure_schema_exists()` for unit-only collection
- [ ] Detect integration tests via `config.args` / `testpaths` (or equivalent)

**Verify:** `make backend-test-unit` does not connect to Postgres when DB service is down.

## Task 5 — Pyproject testpaths

- [ ] Set `[tool.pytest.ini_options] testpaths = ["src/tests/unit", "src/tests/integration"]` in `backend/pyproject.toml`

**Verify:** Default pytest discovery covers both trees.

## Task 6 — Makefile targets

- [ ] Add `backend-test-unit`: `uv run pytest src/tests/unit --no-cov -n auto --dist=loadscope`
- [ ] Add `backend-test-integration`: `uv run pytest src/tests/integration` (inherits cov addopts)
- [ ] Change `backend-test` to sequential unit + integration
- [ ] Document `backend-test-one` requires `unit/` or `integration/` in path

**Verify:** All three targets defined; `.PHONY` updated if needed.

## Task 7 — CI split

- [ ] Add `backend-unit` job: no Postgres service, `--no-cov`, xdist
- [ ] Replace `backend-test` job with `backend-integration`: Postgres + coverage + Codecov
- [ ] Keep `backend-lint` unchanged; parallel job graph (no cross-job `needs`)

**Verify:** Workflow YAML valid; unit job env minimal (`ENV=test` + defaults).

## Task 8 — README and agent docs

- [ ] Update `backend/src/tests/README.md`: layout, classification, make targets, CI jobs
- [ ] Update `.cursor/tech.md`: `make backend-test-unit`, `make backend-test-integration`, `backend-test-one` path prefixes
- [ ] Align rule/skill references if stale paths remain

**Verify:** Docs match implemented targets and directory layout.

## Task 9 — Verify make targets (local Docker)

- [ ] `make backend-test-unit` — green without Postgres
- [ ] `make backend-test-integration` — green with Postgres; `coverage.xml` produced
- [ ] `make backend-test` — full suite green

**Verify:** All three pass inside backend container per design success criteria.

## Task 10 — CI and closeout

- [ ] PR CI: `backend-lint`, `backend-unit`, `backend-integration` all green
- [ ] Codecov upload from integration job only; PR coverage summary unchanged
- [ ] Write `result.md`, `docs/features/backend-test-unit-integration-split.md`
- [ ] Update HOT; append closeout action-log fragment

**Verify:** All success criteria in feature.md checked off.
