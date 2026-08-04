# Feature: backend-test-unit-integration-split

## Scope

Split `backend/src/tests/` into `unit/` and `integration/` trees with directory-based classification, Postgres-free unit runs locally and in CI, and updated Makefile / CI wiring. Single big-bang migration PR — file moves plus runner enforcement; no rewriting DB-backed service tests to mocks in v1.

**Touch points:** `backend/src/tests/`, root `Makefile`, `.github/workflows/ci-backend.yml`, `backend/pyproject.toml`, `tests/support/plugins.py`, agent docs (`.cursor/tech.md`).

**Design:** [docs/superpowers/specs/2026-08-04-backend-unit-integration-test-split-design.md](../../../docs/superpowers/specs/2026-08-04-backend-unit-integration-test-split-design.md)

**Agent guidance:** [`.cursor/rules/backend-unit-integration-tests.mdc`](../../rules/backend-unit-integration-tests.mdc) · [`.cursor/skills/backend-unit-integration-tests/SKILL.md`](../../skills/backend-unit-integration-tests/SKILL.md)

## Non-goals (v1)

- Rewriting DB-backed service tests as mocked unit tests
- Frontend Vitest changes
- Merged coverage gate across CI jobs
- Pytest markers as primary classifier

## Acceptance criteria

- [ ] `backend/src/tests/unit/` and `backend/src/tests/integration/` exist; legacy top-level test domain folders removed
- [ ] `make backend-test-unit` passes without Postgres service running
- [ ] `make backend-test-integration` passes with Postgres and produces `coverage.xml`
- [ ] `make backend-test` runs unit then integration sequentially; all tests green; coverage artifact from integration leg only
- [ ] CI: `backend-lint`, `backend-unit`, `backend-integration` all green; unit job has no Postgres service
- [ ] Fixture guard rejects `prepare_db` / `async_client` under `unit/`
- [ ] Unit-only pytest runs do not connect to Postgres (`pytest_sessionstart` gated)
- [ ] Codecov upload still works from integration job; no regression in PR coverage summary
- [ ] `backend/src/tests/README.md` describes the split and developer workflow
- [ ] No v1 scope creep: DB service tests not rewritten to mocks; no frontend Vitest work; no merged coverage gate
