# .cursor Workflow

Разработка бэкенда и проверки качества по умолчанию ведутся **из Docker** (см. корневой `Makefile`, `docker-compose.yml`, `.cursor/tech.md`).

## 0) Read HOT (session start)

Read [`.cursor/HOT.md`](HOT.md) **first** on every new session. HOT is the **canonical feature registry** for the hot window: which slugs are in progress and the three most recently completed.

- Do **not** glob or list all of `.cursor/active/` or `.cursor/memory/logs/`.
- Do **not** read `.cursor/archive/**` unless the user explicitly asks for historical recovery.
- Deep-read `active/`, log fragments, or `plans/` only for slugs listed in HOT (or named by the user).

## 1) Describe Feature
Create `.cursor/features/<feature-slug>/feature.md` from `.cursor/features/templates/feature-request-template.md`.

## 2) Build Detailed Plan
Create `.cursor/active/<feature-slug>/plan.md` from `.cursor/active/templates/plan-template.md`.

## 3) Execute And Log
- Update `.cursor/active/<feature-slug>/progress.md` after meaningful actions.
- Append **one action-log fragment per milestone or closeout** (not every micro-action); link it from `action-log.md` and keep the index at ≤25 links.

## 4) Finalize (closeout)
- Write `.cursor/active/<feature-slug>/result.md`.
- If the feature changed `backend/`, ship full pytest coverage for that scope (see `.cursor/rules/feature-delivery-workflow.mdc` step 3a) and record verification via Docker (`make backend-test`, etc.; see `.cursor/tech.md`).
- Publish final documentation to `docs/features/<feature-slug>.md`.
- **Update HOT:** move slug from `in_progress` to `recent_completed` (re-sort by closeout date, keep top 3, queue evicted slug for archive).
- Append one closeout fragment to `.cursor/memory/logs/` and trim `action-log.md` to ≤25 links.
