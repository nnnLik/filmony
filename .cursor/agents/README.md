# Agent pipeline (optional)

This folder holds **optional** multi-agent definitions (`business-analyst`, `code-explorer`, `backend-dev`, etc.) used when running the slice-based pipeline.

## Lifecycle source of truth

Feature delivery lifecycle (HOT-first session start, closeout, action-log policy, archive ban) is defined in:

- `.cursor/rules/feature-delivery-workflow.mdc`
- `.cursor/README.md`
- `.cursor/HOT.md` — canonical feature registry for the hot window

Do **not** treat agent markdown or pipeline skills as replacing that workflow.

## When to use agents

- **Default:** follow `.cursor/rules/feature-delivery-workflow.mdc` directly in the main session.
- **Optional multi-agent mode:** invoke the `feature-agent-pipeline` skill when you want slice matrix + agent queue orchestration (see `.cursor/skills/feature-agent-pipeline/SKILL.md`). This skill is **not** always-applied.

## Mechanical delegation

When the always-applied `composer-token-economy-orchestrator` skill is active, the main model delegates mechanical work (search, reads, edits, lint/test runs) to **`composer-common-agent`** subagents only. That skill scopes **how** work is executed, not **what** lifecycle artifacts to produce — those remain under `feature-delivery-workflow.mdc`.
