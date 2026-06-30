# Dependabot Alerts Dependency Update Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clear Dependabot security alerts by applying minor/patch dependency updates in the frontend (npm) and backend (Poetry) with audits and verification.

**Architecture:** Use audit outputs to identify vulnerable packages, update dependencies within existing semver constraints (no major bumps), refresh lockfiles, and verify results with audits plus frontend lint/build and backend tests in Docker.

**Tech Stack:** npm, Poetry, Docker Compose, Makefile, Node.js, Python.

---

I'm using the writing-plans skill to create the implementation plan.

## File Structure Map

- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Modify: `backend/pyproject.toml`
- Modify: `backend/poetry.lock`

### Task 1: Frontend npm security updates (minor/patch only)

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`

- [ ] **Step 1: Capture current npm audit findings**

Run: `cd frontend && npm audit --json`
Expected: JSON output includes `metadata.vulnerabilities` with counts for any current advisories; note package names and ranges from `advisories`/`via` entries.

- [ ] **Step 2: Review outdated versions within semver constraints**

Run: `cd frontend && npm outdated`
Expected: Table output with `Current`, `Wanted`, `Latest`; only proceed with updates where `Wanted` stays within the current major version (no major bumps).

- [ ] **Step 3: Apply minor/patch updates within current ranges**

Run: `cd frontend && npm update`
Expected: npm updates packages to the `Wanted` column without changing major versions; `package-lock.json` is updated.

- [ ] **Step 4: Apply non-breaking audit fixes**

Run: `cd frontend && npm audit fix`
Expected: npm applies audit fixes without `--force`, reporting reduced vulnerability counts and no major version upgrades.

- [ ] **Step 5: Re-run npm audit to verify fixes**

Run: `cd frontend && npm audit`
Expected: `found 0 vulnerabilities` (or only low vulnerabilities with no available minor/patch fixes). If any remaining issue requires a major bump, stop and report it.

- [ ] **Step 6: Run frontend lint**

Run: `cd frontend && npm run lint`
Expected: Exit code 0 with no ESLint errors.

- [ ] **Step 7: Run frontend build**

Run: `cd frontend && npm run build`
Expected: Build completes successfully with exit code 0.

- [ ] **Step 8: Commit frontend dependency updates**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "chore: update frontend deps for dependabot alerts"
```

### Task 2: Backend Poetry security updates in Docker (minor/patch only)

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/poetry.lock`

- [ ] **Step 1: Capture current Python audit findings**

Run: `docker compose -f docker-compose.yml exec backend poetry run pip-audit`
Expected: Audit report lists vulnerable packages and fixed versions (if any).

- [ ] **Step 2: Review outdated top-level packages**

Run: `docker compose -f docker-compose.yml exec backend poetry show --outdated --top-level`
Expected: Table output with `Current` and `Latest` versions; only proceed when updates stay within the current major version.

- [ ] **Step 3: Apply Poetry updates within constraints**

Run: `docker compose -f docker-compose.yml exec backend poetry update`
Expected: `poetry.lock` updated with minor/patch bumps only; no dependency jumps to a new major version.

- [ ] **Step 4: Re-run Python audit to verify fixes**

Run: `docker compose -f docker-compose.yml exec backend poetry run pip-audit`
Expected: `No known vulnerabilities found` (or only vulnerabilities without a minor/patch fix). If any remaining issue requires a major bump, stop and report it.

- [ ] **Step 5: Run backend tests in Docker**

Run: `make backend-test`
Expected: All backend tests pass.

- [ ] **Step 6: Commit backend dependency updates**

```bash
git add backend/pyproject.toml backend/poetry.lock
git commit -m "chore: update backend deps for dependabot alerts"
```

## Self-Review

1. **Spec coverage:** Plan includes npm and Poetry dependency updates, audit checks, and verification steps for frontend and backend.
2. **Placeholder scan:** No TBD/TODO placeholders; commands and expected outputs are explicit.
3. **Type consistency:** Commands and file paths are consistent with project docs and Docker requirements.
