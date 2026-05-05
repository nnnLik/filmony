# .cursor Workflow

Разработка бэкенда и проверки качества по умолчанию ведутся **из Docker** (см. корневой `Makefile`, `compose.yml`, подробные примеры — `.cursor/tech.md`).

## 1) Describe Feature
Create `.cursor/features/<feature-slug>/feature.md` from `.cursor/features/templates/feature-request-template.md`.

## 2) Build Detailed Plan
Create `.cursor/active/<feature-slug>/plan.md` from `.cursor/active/templates/plan-template.md`.

## 3) Execute And Log
- Update `.cursor/active/<feature-slug>/progress.md` after each meaningful action.
- Append the same action to `.cursor/memory/logs/action-log.md`.

## 4) Finalize
- Write `.cursor/active/<feature-slug>/result.md`.
- If the feature changed `backend/`, ship full pytest coverage for that scope (see `.cursor/rules/feature-delivery-workflow.mdc` step 3a) and record verification via Docker (`make backend-test`, etc.; see `.cursor/tech.md`).
- Publish final documentation to `docs/features/<feature-slug>.md`.
