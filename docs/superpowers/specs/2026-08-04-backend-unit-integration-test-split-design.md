# Backend unit / integration test split

**Status:** approved  
**Date:** 2026-08-04  
**Scope:** `backend/src/tests/`, root `Makefile`, `.github/workflows/ci-backend.yml`

### Agent guidance

- Rule: [`.cursor/rules/backend-unit-integration-tests.mdc`](../../../.cursor/rules/backend-unit-integration-tests.mdc)
- Skill: [`.cursor/skills/backend-unit-integration-tests/SKILL.md`](../../../.cursor/skills/backend-unit-integration-tests/SKILL.md)
- Reference: [`.cursor/skills/backend-unit-integration-tests/reference.md`](../../../.cursor/skills/backend-unit-integration-tests/reference.md)

---

## Context

Today all backend tests live under a flat `backend/src/tests/` tree (`api/`, `services/`, `providers/`, `auth/`, `scripts/`, etc.) and share one pytest configuration in `backend/pyproject.toml`. Every CI run and local `make backend-test` starts a Postgres service, runs migrations via `prepare_db`, and collects branch coverage across the full suite.

That model is correct for HTTP and persistence-heavy tests but is expensive for fast feedback:

| Concern | Current state (2026-08-04) | Pain |
|---------|---------------------------|------|
| Local iteration | `make backend-test` always needs Docker Postgres + schema bootstrap | Slow loop for pure logic, DTO parsing, mocked-service tests |
| CI | Single `backend-test` job with Postgres service + coverage upload | Unit-suitable tests wait on DB even when they never touch it |
| Classification | Implicit — anything may request `prepare_db` or `async_client` | No enforced boundary; new tests default to integration cost |
| Layout | Domain folders at top level (`api/`, `services/`, …) | Hard to run “fast only” or “DB only” without ad-hoc `-k` filters |

Shared infrastructure already exists: `tests/support/` (`db_setup.py`, fakes, helpers), `tests/conftest.py` (`pytest_plugins = ('tests.support.plugins',)`), and fixtures `prepare_db` / `async_client` in `tests/support/plugins.py`. The split reuses this support layer; it only partitions **where tests live** and **how they are invoked** locally and in CI.

---

## Goals

1. **Faster local feedback:** Developers can run unit tests without Postgres (`make backend-test-unit`) for sub-minute loops on pure logic and mocked-service tests.
2. **Faster CI signal:** A Postgres-free `backend-unit` job runs on every PR/push; integration tests remain gated on real DB + ASGI as today.
3. **Explicit classification:** Directory placement encodes test type; a light guard prevents accidental DB fixtures under `unit/`.
4. **Preserve full-suite semantics:** `make backend-test` continues to mean “run everything” (unit + integration) so existing docs and muscle memory stay valid.
5. **Domain mirroring:** Both trees mirror product domains (`api`, `services`, `providers`, …) so files are easy to find after migration.
6. **Single migration PR:** Big-bang move in one PR — no long-lived dual layout or per-file opt-in markers.

---

## Non-goals (v1)

- **Rewriting DB-backed service tests as mocked unit tests.** Tests that today use `prepare_db` stay integration; v1 only moves files and splits runners. Converting e.g. `services/search/test_search_my_user_cards_by_title_service.py` to mocked DAO unit tests is follow-up work.
- **Frontend Vitest split or changes.** This design covers backend pytest only.
- **Mandatory merged coverage across jobs.** v1 uploads coverage from the integration job only (same as today). Unit job runs with no coverage or minimal `--cov` locally optional; no Codecov merge gate in v1.
- **Pytest markers as the primary classifier.** Directories are the source of truth; `@pytest.mark.integration` is not required.
- **Changing `backend-lint`.** Ruff check/format job stays identical.

---

## Classification rules

Apply these rules when placing or reviewing a test file during the migration PR.

### Integration (default for uncertainty)

A test file belongs under `backend/src/tests/integration/**` when **any** of the following is true:

| Signal | Examples |
|--------|----------|
| Uses `prepare_db` fixture | Service tests that seed/query real rows |
| Uses `async_client` fixture | Route tests via ASGI + httpx |
| Opens real DB session / DAO against Postgres | Direct `db_setup` usage, migration tests |
| Lives under former `api/` | All HTTP contract tests |
| Lives under `migrations/` | Schema migration verification |
| Lives under `scripts/` with DB side effects | Backfill/diagnostic CLI flows against test DB |
| **Ambiguous** — could be unit or integration | **Classify as integration** (safe default) |

**Heuristic summary:**

- **`api/` → integration** — always (ASGI client + auth + routing).
- **`services/` → mixed** — inspect fixtures:
  - `prepare_db` / `async_client` / real DAO → **integration**
  - pure functions, DTO mapping, mocked collaborators only → **unit**
- **Everything else** — case-by-case; when in doubt → **integration**.

### Unit

A test file belongs under `backend/src/tests/unit/**` when **all** of the following hold:

| Requirement | Detail |
|-------------|--------|
| No real Postgres | Must not use `prepare_db`, `async_client`, or call `db_setup` |
| No ASGI app | No httpx client against FastAPI app |
| Deterministic & isolated | Mocks/fakes/stubs for DAOs, HTTP clients, Celery, external APIs |
| In scope for v1 | **Pure logic** (parsers, scoring, slug helpers) and **existing** mock-only service tests. The `unit/` tree also accepts **future** mocked-DAO service tests; rewriting DB-backed services to mocks is **out of scope** in v1 (see [Non-goals](#non-goals-v1)) |

**Examples that stay or move to unit (after rewrite or if already mock-only):**

- `lib/test_genre_slug.py`, `providers/test_youtube_url.py` — pure helpers
- `services/taste_quiz/test_scoring.py` — domain logic without DB
- `services/franchises/test_franchise_label.py` — string/label rules
- Future: service orchestration tested with `AsyncMock` DAOs (out of scope to rewrite in v1, but directory is ready)

**Examples that stay integration:**

- All of `api/test_*`
- `services/search/test_search_my_user_cards_by_title_service.py` (uses `prepare_db`)
- `migrations/test_watchlist_migration.py`
- `scripts/test_manage_backfill_film_gamification_metadata.py`

---

## Directory layout

```
backend/src/tests/
├── conftest.py                 # unchanged root: env, pytest_plugins
├── README.md                   # updated: unit vs integration, make targets
├── support/                    # shared — NOT under unit/ or integration/
│   ├── plugins.py              # prepare_db, async_client (integration-only fixtures)
│   ├── db_setup.py
│   └── …
├── unit/
│   ├── lib/
│   ├── providers/
│   ├── services/
│   │   ├── taste_quiz/
│   │   ├── franchises/
│   │   └── …
│   ├── auth/                   # session/JWT parsing without DB, if applicable
│   └── …
└── integration/
    ├── api/
    ├── services/
    ├── migrations/
    ├── scripts/
    ├── tasks/
    ├── models/                 # schema tests touching DB
    └── …
```

**Rules:**

- **`support/` remains sibling to `unit/` and `integration/`** — shared fakes, helpers, and plugin fixtures.
- **Mirror domain segments** inside each tree (`services/cards/`, `services/catalog/`, etc.) so paths differ only by the `unit/` or `integration/` prefix.
- **No duplicate conftest hierarchy required in v1.** Root `conftest.py` + `support/plugins.py` suffice; optional `integration/conftest.py` only if needed later.
- **Top-level legacy folders removed** after migration (`api/`, `services/`, … at `tests/` root) — big-bang PR moves all files.

---

## Fixtures & enforcement

### Fixture ownership

| Fixture | Defined in | Allowed in |
|---------|------------|------------|
| `prepare_db` | `tests/support/plugins.py` | `integration/**` only |
| `async_client` | `tests/support/plugins.py` (depends on `prepare_db`) | `integration/**` only |
| Shared fakes (`fake_kinopoisk_*`, helpers) | `tests/support/` | both trees |
| Autouse patches (e.g. TMDB sync noop) | `tests/support/plugins.py` | both trees (harmless for unit) |

### Enforcement mechanism (v1 — light guard)

Add a pytest hook or small autouse fixture in `tests/unit/conftest.py` that **fails collection** if a test under `unit/` requests forbidden fixtures:

```python
_FORBIDDEN_IN_UNIT = frozenset({'prepare_db', 'async_client'})


def pytest_collection_modifyitems(session, config, items):
    for item in items:
        if '/unit/' not in item.fspath.strpath:
            continue
        for name in item.fixturenames:
            if name in _FORBIDDEN_IN_UNIT:
                raise pytest.UsageError(
                    f'{item.nodeid}: fixture {name!r} is not allowed under tests/unit/'
                )
```

**Not in v1:** AST importers scanning for `db_setup` imports, mandatory `@pytest.mark.integration`, or banning `support/` imports from unit tests.

### Pytest paths

Update `backend/pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["src/tests/unit", "src/tests/integration"]
```

Default `addopts` (xdist + coverage) apply to **`backend-test-integration`** and the integration leg of **`backend-test`**; **`backend-test-unit`** passes `--no-cov` (see Makefile).

### Session bootstrap (required for Postgres-free unit runs)

`pytest_sessionstart` in `plugins.py` currently calls `db_setup.ensure_schema_exists()` and connects to Postgres on every pytest invocation — including unit-only runs. That **blocks** `make backend-test-unit` and the CI `backend-unit` job without Postgres.

**Migration PR must gate schema bootstrap:** call `ensure_schema_exists()` only when integration tests are in the collected set (e.g. check `config.args` / `testpaths` for `integration`, or skip when `--collect-only` under `unit/` only). Unit collection must not open a DB connection.

---

## Makefile

Add explicit targets; keep `backend-test` as the union.

| Target | Command (inside `filmony-backend` container) | Postgres | Coverage |
|--------|-----------------------------------------------|----------|----------|
| `backend-test-unit` | `uv run pytest src/tests/unit --no-cov -n auto --dist=loadscope` | not required | off |
| `backend-test-integration` | `uv run pytest src/tests/integration` (inherits `addopts` cov) | required | on (as today) |
| `backend-test` | `backend-test-unit` then `backend-test-integration` (sequential) | required for integration leg | integration leg only (see [Coverage v1 policy](#ci)) |
| `backend-test-one` | unchanged UX; path must include `unit/` or `integration/` prefix | depends on target | `--no-cov` (unchanged) |

**Implementation sketch:**

```makefile
backend-test-unit:
	$(AEXEC_NO_TTY) $(APP) uv run pytest src/tests/unit --no-cov -n auto --dist=loadscope

backend-test-integration:
	$(AEXEC_NO_TTY) $(APP) uv run pytest src/tests/integration

backend-test: backend-test-unit backend-test-integration
```

Document in `backend/src/tests/README.md` that local fast loop is `make backend-test-unit` with Docker backend container up but **without** requiring Postgres for unit-only runs (backend container can start; DB service optional for unit).

---

## CI

Workflow: `.github/workflows/ci-backend.yml`

| Job | Change | Postgres service | Tests | Coverage |
|-----|--------|------------------|-------|----------|
| `backend-lint` | **unchanged** | — | ruff check + format | — |
| `backend-unit` | **new** | **none** | `uv run pytest src/tests/unit --no-cov -n auto --dist=loadscope` | none |
| `backend-integration` | **replaces** current `backend-test` job name | yes (same as today) | `uv run pytest src/tests/integration` | yes — `coverage.xml`, htmlcov, Codecov upload, PR summary |

**Job graph:** `backend-lint`, `backend-unit`, and `backend-integration` run in parallel (no `needs` between them).

**Environment:** Integration job keeps current `env` block (`DATABASE_URL`, `DATABASE_TEST_URL`, API keys, Celery broker). Unit job sets only what pure tests need (`ENV=test`, placeholder keys already defaulted in `conftest.py`).

**Coverage v1 policy:**

- Integration job = **authoritative** line/branch coverage for Codecov (same as today).
- Unit job = **no** coverage upload; optional local `--cov=src --cov-report=term` for debugging only.
- No merged coverage artifact or fail-under gate combining both jobs in v1.

---

## Migration plan (PR steps)

Single PR — **big-bang** file moves plus runner/CI wiring.

1. **Branch:** e.g. `chore/backend-test-unit-integration-split`.

2. **Create directories:**
   - `backend/src/tests/unit/` with mirrored subfolders.
   - `backend/src/tests/integration/` with mirrored subfolders.

3. **Classify and `git mv` every test module** using [Classification rules](#classification-rules):
   - All `api/**` → `integration/api/**`
   - Each `services/**` file → `unit/services/**` or `integration/services/**` per fixtures
   - `providers/`, `lib/`, `auth/` (non-DB) → mostly `unit/`
   - `migrations/`, `scripts/`, DB-heavy `tasks/`, `models/` → `integration/`
   - Leave `support/`, root `conftest.py` in place

4. **Add `tests/unit/conftest.py`** with the fixture guard (see [Fixtures & enforcement](#fixtures--enforcement)).

5. **Gate `pytest_sessionstart` schema bootstrap** in `tests/support/plugins.py` so unit-only runs do not connect to Postgres (see [Session bootstrap](#session-bootstrap-required-for-postgres-free-unit-runs)).

6. **Update `backend/pyproject.toml`** `testpaths` to both trees.

7. **Update root `Makefile`:** add `backend-test-unit`, `backend-test-integration`; change `backend-test` to run both.

8. **Update `.github/workflows/ci-backend.yml`:** split `backend-test` into `backend-unit` + `backend-integration`.

9. **Update `backend/src/tests/README.md`:** document layout, classification, make targets, CI jobs.

10. **Verify locally (Docker):**
   - `make backend-test-unit` — passes without Postgres
   - `make backend-test-integration` — passes with Postgres
   - `make backend-test` — full suite green

11. **Verify CI:** all three jobs green on the PR; Codecov still fed from integration artifacts only.

12. **Update agent docs** (optional same PR or immediate follow-up): `.cursor/tech.md` and `feature-delivery-workflow` references to `make backend-test-one` paths with new prefixes.

**Import paths:** test modules keep `from tests.support…` imports; no production code changes. pytest node IDs gain the `unit/` or `integration/` segment — update any hard-coded paths in docs or scripts.

---

## Risks

| Risk | Mitigation |
|------|------------|
| Misclassified test lands in `unit/` but needs DB | Fixture guard fails fast at collection; code review checklist uses fixture grep |
| Misclassified test in `integration/` slows unit job | Wrong direction only affects integration job; unit job unaffected |
| `pytest_sessionstart` schema bootstrap without Postgres | Gate `ensure_schema_exists()` to integration collection only in migration PR (see [Session bootstrap](#session-bootstrap-required-for-postgres-free-unit-runs)) |
| Developer runs `backend-test-integration` without local Postgres | Existing Docker-first docs unchanged; error message from `db_setup` |
| xdist + integration flakiness | Keep `--dist=loadscope` on both; integration retains worker schema env from `xdist_bootstrap` |
| Coverage drop reported on Codecov | Integration job still covers DB/HTTP paths; unit-only files may lower **reported** coverage until rewritten — accepted in v1; document in PR |
| Large PR hard to review | Provide classification table in PR description (source → destination counts by folder) |

---

## Success criteria

- [ ] `backend/src/tests/unit/` and `backend/src/tests/integration/` exist; legacy top-level test domain folders removed.
- [ ] `make backend-test-unit` passes without Postgres service running.
- [ ] `make backend-test-integration` passes with Postgres and produces `coverage.xml`.
- [ ] `make backend-test` runs unit then integration sequentially; all tests green; coverage artifact produced from integration leg only.
- [ ] CI: `backend-lint`, `backend-unit`, `backend-integration` all green; unit job has no Postgres service.
- [ ] Fixture guard rejects `prepare_db` / `async_client` under `unit/`.
- [ ] Unit-only pytest runs do not connect to Postgres (`pytest_sessionstart` gated).
- [ ] Codecov upload still works from integration job; no regression in PR coverage summary.
- [ ] `backend/src/tests/README.md` describes the split and developer workflow.
- [ ] No v1 scope creep: DB service tests not rewritten to mocks; no frontend Vitest work; no merged coverage gate.
