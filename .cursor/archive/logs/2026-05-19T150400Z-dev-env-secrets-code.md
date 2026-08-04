Timestamp: 2026-05-19T150400Z
Feature slug: dev-env-secrets
Action type: code
Summary: Split local dev configuration into a tracked defaults file and a gitignored secrets file, then loaded both from docker-compose for dev only.
Files:
- docker-compose.yml
- vars/.env.development
- vars/.env.development.secrets
- .gitignore
Verification: Manual review of the edited env and compose files; no runtime checks were required for this config-only change.
