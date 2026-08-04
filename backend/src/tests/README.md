# Backend tests (`src/tests`)

Pytest suite split into **unit** (fast, no Postgres) and **integration** (DB, ASGI, HTTP). Directories are the source of truth — not pytest markers.

## Layout

```
src/tests/
├── conftest.py          # root env, pytest_plugins
├── support/             # shared fakes, db_setup, plugins — NOT under unit/ or integration/
├── unit/                # pure logic, mock-only services (mirror domains: lib/, services/, …)
└── integration/         # prepare_db, async_client, api/, migrations/, DB scripts
```

Mirror domain folders inside each tree (`services/cards/`, `api/`, etc.). Legacy flat folders at `tests/` root are removed after migration.

## Classification (short)

| Type | Signals |
|------|---------|
| **Unit** | No `prepare_db`, no `async_client`, no real DB/ASGI; mocks/fakes only |
| **Integration** | Any DB fixture, real DAO, HTTP route test; **ambiguous → integration** |

All `api/` tests are integration. `services/` is mixed — inspect fixtures.

## Run (Docker-first)

From repo root, inside the `backend` container (see `.cursor/tech.md`). Split-specific Make targets are per the approved design; until they land, use `make backend-test` / `make backend-test-one`.

| Command | Postgres | Notes |
|---------|----------|-------|
| `make backend-test-unit` | not required | Fast local loop |
| `make backend-test-integration` | required | Coverage as today |
| `make backend-test` | required for integration leg | Full suite (unit then integration) |
| `make backend-test-one target=src/tests/unit/…` | depends on path | Must include `unit/` or `integration/` prefix |

Integration tests need `DATABASE_TEST_URL` pointing at `filmony_test` (schema `public`).

## Agent docs

- Design: [`docs/superpowers/specs/2026-08-04-backend-unit-integration-test-split-design.md`](../../../docs/superpowers/specs/2026-08-04-backend-unit-integration-test-split-design.md)
- Skill: [`.cursor/skills/backend-unit-integration-tests/SKILL.md`](../../../.cursor/skills/backend-unit-integration-tests/SKILL.md)
- Rule: [`.cursor/rules/backend-unit-integration-tests.mdc`](../../../.cursor/rules/backend-unit-integration-tests.mdc)
