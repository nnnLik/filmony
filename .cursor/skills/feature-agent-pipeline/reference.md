# Handoff prompt templates

Use these as shells; replace placeholders with real content from the session.

## Task: business-analyst

```text
Feature slug: {slug}
Repository: kino (Filmony). Follow kino docs under docs/ and .cursor/rules/.

USER_FEATURE:
{paste feature + links + screenshots summary}

ADDITIONAL_CONTEXT:
{paste}

Deliver: full SPEC + SLICE_MATRIX + AGENT_QUEUE per your agent instructions.
Flag open questions if any blockers.
```

## Task: code-explorer

```text
Feature slug: {slug}

SPEC (from BA):
{paste full SPEC}

Optional — SLICE_MATRIX (if present, scope the map to slices):
{paste or "N/A"}

Task: Produce the required report (affected modules, files to change, dependencies, risks).
Do not propose solutions. Map to this repo’s backend/ and frontend/ layout.
```

## Task: backend-dev

```text
Feature slug: {slug}

ACTIVE_SLICE: {e.g. S2}

SLICE_SPEC (this Task only — do not implement other slices):
{paste narrow AC + scope from SLICE_MATRIX}

Out of scope for this Task (reference only):
{other slice IDs or "none"}

FILES / AREAS (from code-explorer, scoped to this slice):
{paste CODE_MAP}

Full SPEC (reference only):
{paste full SPEC or link to progress.md}

kino constraints: FastAPI backend under backend/, pytest in Docker via Makefile targets
(see .cursor/tech.md). Obey .cursor/rules/backend-fastapi-standards.mdc and
feature-delivery-workflow for .cursor/active/{slug}/ and tests.

Implement this slice only; include test evidence in your reply.
```

## Task: frontend-dev

```text
Feature slug: {slug}

ACTIVE_SLICE: {e.g. S3}

SLICE_SPEC (this Task only):
{paste narrow AC + scope from SLICE_MATRIX}

Out of scope for this Task:
{other slice IDs or "none"}

FILES / AREAS (from code-explorer, frontend only, scoped to this slice):
{paste relevant CODE_MAP section}

Full SPEC (reference only):
{paste or link}

kino constraints: React + Vite under frontend/, @telegram-apps/telegram-ui, lucide-react.
Obey .cursor/rules/frontend-react-telegram-ui-standards.mdc, docs/frontend/ui-conventions.md,
and feature-delivery-workflow for .cursor/active/{slug}/ and action logs.

After edits: npm run lint && npm run build in frontend/. Report results in your reply.
```

## Task: code-reviewer

```text
Feature slug: {slug}

Review scope: {one slice SX | cumulative feature | per AGENT_QUEUE}

SPEC:
{paste}

CHANGES:
{git diff or file list + summary — include both backend/ and frontend/ when applicable}

Review per your agent format; no code edits.
```
