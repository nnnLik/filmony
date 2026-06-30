# Dependabot Alerts

## Summary
Expose Dependabot vulnerability alerts inside Filmony so maintainers can review, triage, and prioritize dependency fixes without leaving the product.

## Problem
Dependabot alerts currently live only in GitHub. The team lacks a centralized, in-app view of open alerts, their severities, and affected packages.

## Goals
- Provide a backend endpoint to list cached Dependabot alerts.
- Allow a manual refresh that pulls the latest alerts from GitHub and persists them.
- Add an admin-facing UI screen that lists alerts with severity, package, summary, and advisory links.

## Non-goals
- Auto-fix or upgrade dependencies.
- Replace GitHub Dependabot workflows.
- Notify end users; this is admin-only.

## Acceptance Criteria
- An admin can open the Dependabot Alerts screen and see open alerts sorted by severity and update time.
- Refreshing alerts updates the cached list from GitHub within a single request.
- Backend list endpoint returns a typed payload with all fields needed for the UI.
- Backend refresh endpoint and list endpoint are covered by tests run in Docker.

## Dependencies / Assumptions
- A GitHub API token is available in environment configuration.
- Only repository maintainers can access the alert endpoints.
