## Overview
Define a safe, aggressive Dependabot update strategy that clears security alerts by
automatically opening minor/patch updates for frontend npm and backend poetry
dependencies, while explicitly avoiding majors.

## Scope
- Frontend: `frontend/` npm ecosystem.
- Backend: `backend/` poetry ecosystem.
- Update scope: minor/patch only; major updates are excluded.
- Output: Dependabot PRs grouped where safe to minimize churn.

## Approach
- Configure Dependabot to scan frontend npm and backend poetry on a regular cadence.
- Allow only minor/patch updates for both ecosystems.
- Group updates to reduce PR volume while keeping risk contained.
- Keep existing lockfiles authoritative and updated by Dependabot.
- No git operations or commits are part of this spec.

## Data/Execution Flow
1. Dependabot scans `frontend/` (npm) and `backend/` (poetry).
2. For each ecosystem, Dependabot evaluates available versions.
3. Updates are filtered to minor/patch only and grouped where applicable.
4. Dependabot opens PRs with updated manifests/lockfiles.
5. CI checks run per PR (backend tests in Docker, frontend lint/build).

## Risks
- Minor/patch changes can still introduce regressions.
- Grouped updates may complicate pinpointing a single problematic package.
- Lockfile churn can create merge conflicts with concurrent dependency changes.

## Testing/Verification
- Backend: run tests inside Docker (`make backend-test` or `make backend-test-one`).
- Frontend: `cd frontend && npm run lint && npm run build`.
- Validate Dependabot PRs pass CI before merge.

## Rollback
- Revert or close the Dependabot PR that introduced regressions.
- Reapply the previous lockfile and manifest versions if needed.
