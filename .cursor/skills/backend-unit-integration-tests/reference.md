# Backend unit vs integration — reference

Design spec: [`docs/superpowers/specs/2026-08-04-backend-unit-integration-test-split-design.md`](../../../docs/superpowers/specs/2026-08-04-backend-unit-integration-test-split-design.md)  
Rule: [`.cursor/rules/backend-unit-integration-tests.mdc`](../../rules/backend-unit-integration-tests.mdc)  
Skill: [`SKILL.md`](SKILL.md)

---

## Integration signals (any one → `integration/`)

| Signal | Examples |
|--------|----------|
| Uses `prepare_db` fixture | Service tests that seed/query real rows |
| Uses `async_client` fixture | Route tests via ASGI + httpx |
| Opens real DB session / DAO against Postgres | Direct `db_setup` usage, migration tests |
| Lives under former `api/` | All HTTP contract tests |
| Lives under `migrations/` | Schema migration verification |
| Lives under `scripts/` with DB side effects | Backfill/diagnostic CLI flows against test DB |
| **Ambiguous** — could be unit or integration | **Classify as integration** (safe default) |

## Unit requirements (all must hold → `unit/`)

| Requirement | Detail |
|-------------|--------|
| No real Postgres | Must not use `prepare_db`, `async_client`, or call `db_setup` |
| No ASGI app | No httpx client against FastAPI app |
| Deterministic & isolated | Mocks/fakes/stubs for DAOs, HTTP clients, Celery, external APIs |
| In scope for v1 | Pure logic and existing mock-only service tests; future mocked-DAO service tests welcome — rewriting DB-backed services to mocks is **out of scope** in v1 |

### Examples

**Unit (move or keep after classification):**

- `lib/test_genre_slug.py`, `providers/test_youtube_url.py` — pure helpers
- `services/taste_quiz/test_scoring.py` — domain logic without DB
- `services/franchises/test_franchise_label.py` — string/label rules

**Integration (always):**

- All of `api/test_*`
- `services/search/test_search_my_user_cards_by_title_service.py` (uses `prepare_db`)
- `migrations/test_watchlist_migration.py`
- `scripts/test_manage_backfill_film_gamification_metadata.py`

---

## Makefile targets

Targets below are the approved contract; until the split PR lands, use `make backend-test` / `make backend-test-one`.

| Target | Command (inside `filmony-backend` container) | Postgres | Coverage |
|--------|-----------------------------------------------|----------|----------|
| `backend-test-unit` | `uv run pytest src/tests/unit --no-cov -n auto --dist=loadscope` | not required | off |
| `backend-test-integration` | `uv run pytest src/tests/integration` (inherits `addopts` cov) | required | on (as today) |
| `backend-test` | `backend-test-unit` then `backend-test-integration` (sequential) | required for integration leg | integration leg only |
| `backend-test-one` | unchanged UX; path must include `unit/` or `integration/` prefix | depends on target | `--no-cov` |

Local fast loop: `make backend-test-unit` with backend container up; Postgres service optional for unit-only runs.

---

## CI jobs (`.github/workflows/ci-backend.yml`)

| Job | Postgres service | Tests | Coverage |
|-----|------------------|-------|----------|
| `backend-lint` | — | ruff check + format | — |
| `backend-unit` | **none** | `uv run pytest src/tests/unit --no-cov -n auto --dist=loadscope` | none |
| `backend-integration` | yes (same as today) | `uv run pytest src/tests/integration` | yes — `coverage.xml`, htmlcov, Codecov upload |

Jobs run in parallel (no `needs` between lint, unit, integration). Integration job is **authoritative** for Codecov; no merged coverage gate in v1.

---

## Fixture ownership

| Fixture | Defined in | Allowed in |
|---------|------------|------------|
| `prepare_db` | `tests/support/plugins.py` | `integration/**` only |
| `async_client` | `tests/support/plugins.py` (depends on `prepare_db`) | `integration/**` only |
| Shared fakes (`fake_kinopoisk_*`, helpers) | `tests/support/` | both trees |
| Autouse patches (e.g. TMDB sync noop) | `tests/support/plugins.py` | both trees |

### Collection guard (`tests/unit/conftest.py`)

Fails collection if a test under `unit/` requests `prepare_db` or `async_client`:

```python
_FORBIDDEN_IN_UNIT = frozenset({'prepare_db', 'async_client'})
```

**Not in v1:** AST scans for `db_setup` imports, mandatory `@pytest.mark.integration`, or banning `support/` imports from unit tests.

### Session bootstrap

`pytest_sessionstart` in `plugins.py` must gate `ensure_schema_exists()` so unit-only runs do not connect to Postgres.

---

## Migration heuristics

| Source folder | Destination |
|---------------|-------------|
| `api/**` | `integration/api/**` (always) |
| `services/**` | Inspect fixtures: `prepare_db`/`async_client`/real DAO → `integration/services/**`; mocks/pure logic → `unit/services/**` |
| `providers/`, `lib/`, non-DB `auth/` | Mostly `unit/` |
| `migrations/`, `scripts/`, DB-heavy `tasks/`, `models/` | `integration/` |
| `support/`, root `conftest.py` | Stay in place |

When in doubt → **integration**. Legacy top-level domain folders are removed after big-bang migration.

---

## Out of scope (v1)

- Rewriting DB-backed service tests as mocked unit tests (classification + move only)
- Frontend Vitest split or changes
- Mandatory merged coverage across unit + integration jobs
- Pytest markers as primary classifier
- Changes to `backend-lint`

---

## Pytest configuration

```toml
[tool.pytest.ini_options]
testpaths = ["src/tests/unit", "src/tests/integration"]
```

Default `addopts` (xdist + coverage) apply to integration runs and the integration leg of `backend-test`; `backend-test-unit` passes `--no-cov`.
