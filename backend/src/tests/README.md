# Backend tests (`src/tests`)

Pytest suite split into **unit** (fast, no Postgres) and **integration** (DB, ASGI, HTTP). Directories are the source of truth — not pytest markers.

## Layout

```
src/tests/
├── conftest.py          # root env, pytest_plugins
├── auth/                # shared auth helpers (e.g. telegram initData signing)
├── support/             # shared fakes, db_setup, plugins — NOT under unit/ or integration/
├── unit/
│   ├── conftest.py      # collection guard (forbids prepare_db / async_client)
│   ├── lib/
│   ├── providers/
│   ├── services/
│   └── auth/            # pure auth logic (e.g. session JWT)
└── integration/
    ├── api/             # all HTTP route tests
    ├── auth/
    ├── migrations/
    ├── models/
    ├── scripts/
    ├── services/
    ├── support/         # integration-only support tests (db_setup, xdist bootstrap)
    └── tasks/
```

Mirror domain folders inside each tree (`services/cards/`, `api/`, etc.). Legacy flat folders at `tests/` root (former top-level `api/`, `services/`, …) are removed.

## Classification (short)

| Type | Signals |
|------|---------|
| **Unit** | No `prepare_db`, no `async_client`, no real DB/ASGI; mocks/fakes only |
| **Integration** | Any DB fixture, real DAO, HTTP route test; **ambiguous → integration** |

All `api/` tests live under `integration/api/`. `services/` is split by fixture usage — inspect before placing.

## Run (Docker-first)

From repo root, inside the `backend` container (see `.cursor/tech.md`).

| Command | Postgres | Notes |
|---------|----------|-------|
| `make backend-test-unit` | not required | Fast local loop; `--no-cov`, xdist |
| `make backend-test-integration` | required | Coverage as today |
| `make backend-test` | required for integration leg | Full suite (unit then integration) |
| `make backend-test-one target=src/tests/unit/…` | depends on path | Must include `unit/` or `integration/` prefix; `--no-cov -n0` |

Integration tests need `DATABASE_TEST_URL` pointing at `filmony_test` (schema `public`).

Unit-only runs skip Postgres schema bootstrap (`plugins.py` gate); integration collection or default `testpaths` still bootstrap the test DB.

## CI (`.github/workflows/ci-backend.yml`)

| Job | Postgres | Scope |
|-----|----------|-------|
| `backend-lint` | — | ruff check + format |
| `backend-unit` | **none** | `src/tests/unit` — `--no-cov`, xdist |
| `backend-integration` | yes | `src/tests/integration` — coverage + Codecov |

Lint, unit, and integration jobs run in parallel. Integration job is authoritative for Codecov in v1 (no merged coverage gate).

## Agent docs

- Design: [`docs/superpowers/specs/2026-08-04-backend-unit-integration-test-split-design.md`](../../../docs/superpowers/specs/2026-08-04-backend-unit-integration-test-split-design.md)
- Skill: [`.cursor/skills/backend-unit-integration-tests/SKILL.md`](../../../.cursor/skills/backend-unit-integration-tests/SKILL.md)
- Rule: [`.cursor/rules/backend-unit-integration-tests.mdc`](../../../.cursor/rules/backend-unit-integration-tests.mdc)
