---
name: backend-unit-integration-tests
description: >-
  Classifies and writes backend pytest as unit or integration under
  tests/unit vs tests/integration, with correct fixtures and Make/CI targets.
  Use when adding or moving backend tests, choosing unit vs integration,
  mocking DAOs, or optimizing pytest runs.
---

# Backend Unit vs Integration Tests

Rule: [`.cursor/rules/backend-unit-integration-tests.mdc`](../../rules/backend-unit-integration-tests.mdc)  
Deep reference: [reference.md](reference.md)  
Design spec: [`docs/superpowers/specs/2026-08-04-backend-unit-integration-test-split-design.md`](../../../docs/superpowers/specs/2026-08-04-backend-unit-integration-test-split-design.md)

## When to use

- Adding or moving a backend test module
- Choosing unit vs integration for a new service or route test
- Deciding whether to mock DAOs or use `prepare_db`
- Running fast local loops vs full DB/HTTP coverage
- Reviewing test placement during or after the unit/integration migration

**Note:** Layout may be mid-migration (legacy flat folders still present). Always classify by the rules below and place under `unit/` or `integration/` paths from the design — not legacy top-level folders.

## Workflow checklist

1. **Identify signals** — grep the test (or planned test) for `prepare_db`, `async_client`, `db_setup`, real DAO usage, or ASGI client.
2. **Classify** — if **any** integration signal → `integration/`; if **all** unit requirements hold → `unit/`; if unsure → `integration/`.
3. **Pick path** — mirror domain under the chosen tree, e.g. `unit/services/franchises/test_franchise_label.py`.
4. **Pick fixtures** — unit: mocks/fakes only; integration: `prepare_db` / `async_client` as needed; shared fakes from `tests/support/`.
5. **Run the right target** — `make backend-test-unit` for unit-only; `make backend-test-integration` for DB/HTTP; `make backend-test` before merge.
6. **Verify guard** — unit files must not request forbidden fixtures (`prepare_db`, `async_client`).

## Decision checklist (unit vs integration)

**Integration** when **any** of:

- [ ] Uses `prepare_db` or `async_client`
- [ ] Opens real DB session / DAO against Postgres
- [ ] HTTP route test (ASGI + httpx)
- [ ] Under `api/`, `migrations/`, DB-side-effect `scripts/`
- [ ] Ambiguous — default to integration

**Unit** only when **all** of:

- [ ] No Postgres, no `prepare_db`, no `async_client`, no ASGI app
- [ ] Deterministic with mocks/fakes/stubs for DAOs and external clients
- [ ] Pure logic or mock-only service orchestration

## Where to put the file

```
backend/src/tests/
├── support/          # shared — NOT under unit/ or integration/
├── unit/
│   ├── lib/
│   ├── providers/
│   ├── services/
│   └── …
└── integration/
    ├── api/
    ├── services/
    ├── migrations/
    └── …
```

Mirror domain segments inside each tree (`services/cards/`, `services/catalog/`, etc.).

## Fixture rules

| Fixture | Allowed in |
|---------|------------|
| `prepare_db`, `async_client` | `integration/**` only |
| Shared fakes (`fake_kinopoisk_*`, helpers) | both trees |
| Autouse patches in `support/plugins.py` | both trees |

Unit collection guard rejects `prepare_db` / `async_client` under `unit/`. Markers are **not** the primary classifier.

## How to run

Run pytest **inside** the `backend` container (see `.cursor/tech.md`). Make targets below are the approved contract; until they exist in the Makefile, use `make backend-test` or `make backend-test-one target=src/tests/unit/…` (or `integration/…`).

| Command | Postgres | Coverage |
|---------|----------|----------|
| `make backend-test-unit` | not required | off (`--no-cov`) |
| `make backend-test-integration` | required | on (as today) |
| `make backend-test` | required for integration leg | integration leg only |
| `make backend-test-one target=src/tests/unit/…` | depends on path | `--no-cov` |

CI: `backend-unit` (no Postgres) and `backend-integration` (Postgres + Codecov) run in parallel; `backend-lint` unchanged.

## Out of scope (v1)

- Rewriting DB-backed service tests as mocked unit tests (move only; rewrite is follow-up)
- Frontend Vitest changes
- Merged coverage gate across unit + integration jobs

See [reference.md](reference.md) for full classification tables, Makefile/CI details, and migration heuristics.
