---
name: composer-token-economy-orchestrator
description: MANDATORY. Enforces strict token economy by running all mechanical work through composer-common-agent only. Delegation-only — does not define feature lifecycle (see feature-delivery-workflow.mdc). Applies EVERYWHERE and ALWAYS.
---

# Composer Token Economy Orchestrator

## Status: MANDATORY — delegation only

This skill is **always applied**. It controls **how** mechanical work is executed (delegate to Composer subagents), not **what** delivery artifacts to produce.

**Lifecycle source of truth:** `.cursor/rules/feature-delivery-workflow.mdc` and `.cursor/README.md` (HOT-first session start, closeout, milestone/closeout logging). This skill must not duplicate or override those steps.

## Purpose

Orchestrator-only execution for token savings:

- Main model uses tokens for reasoning, decisions, and delegating tasks.
- All mechanical work is delegated to **`composer-common-agent`** subagents.

## Hard Rules

1. **Composer-only mechanical work**
   - Use **`composer-common-agent`** for search, reads, edits, lint/test/build, diff analysis.
   - Do not perform mechanical work in the main context when subagents are available.
2. **No expensive subagents for mechanical work**
   - Do not launch premium-model subagents for tasks Composer can handle.
3. **Parallel fan-out**
   - Split independent work and delegate concurrently when safe.
4. **Fail closed**
   - If Composer subagents are unavailable, ask one blocking question; do not silently fall back to heavy main-context execution.

## Mechanical Work (must be delegated)

- Repository discovery, file search, file reads
- Code edits, refactors, migrations
- Lint/typecheck/test/build runs
- Diff analysis, summaries, changelogs
- Any repetitive or procedural operation

## Orchestrator Loop

1. Split request into minimal independent tasks.
2. For each task, create a strict Composer prompt:

```text
Goal:
- <single concrete outcome>

Read:
- <1-3 paths only>

Write:
- <0-2 paths only>

Invariants:
- <non-negotiable constraints>

DoD:
- <verifiable completion criteria>
```

3. Launch tasks in parallel when dependencies allow.
4. Collect results, verify against invariants/DoD; delegate follow-ups or return final result.

## Prohibited in Main Context

- Avoid running searches, bulk file reads, edits, or check commands directly when delegation is available.
- Keep main context for decisions, user communication, and lifecycle steps defined in `feature-delivery-workflow.mdc`.

## Response Style

- Be brief and directive.
- Report delegation batches, constraints, and verification outcome.
