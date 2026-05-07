---
name: feature-agent-pipeline
description: >
  Multi-step feature delivery driven by `.cursor/agents/`: business-analyst outputs slice matrix + agent queue;
  each implementation Task gets one slice only; handoff grows per slice (notes, optional review gates).
  Use for full pipelines or agent-driven delivery.
disable-model-invocation: false
---

# Feature agent pipeline (kino)

## Goal

Take a **feature** and **optional context** from the user, then **fully implement** it by:

1. Loading every agent definition under **`.cursor/agents/`** (Markdown files; each file’s YAML `name` is the agent id).
2. **Following the slice matrix and agent queue** from `business-analyst` when present (mandatory output of that agent): **several small Tasks** for implementation instead of one monolithic “whole feature” prompt—even for **backend-only** or **frontend-only** work.
3. **Ordering** which agents run and in what sequence (including **loops** when a gate fails or a slice needs rework).
4. **Handing off** structured outputs from each step as **required inputs** for the next, until the feature meets this repo’s delivery rules (see **Repository integration**).

Canonical agent folder path: **`.cursor/agents/`** (not `Agence`; if the user says “Agence”, treat it as this folder).

## Slice-first orchestration (contract with `business-analyst`)

After step 1 (`business-analyst`), the Handoff must include:

- **`SPEC`**: full TZ for the feature (unchanged purpose for reviewers and traceability).
- **`SLICE_MATRIX`**: table of slices (`S1`, `S2`, …)—goals, artifacts, dependencies, **acceptance criteria per slice only**.
- **`AGENT_QUEUE`**: ordered steps from BA: `Шаг N — agent — slice SX — one-line goal`, plus **«После шага N зафиксировать»** and **«Контрольная точка»** (e.g. append progress, `code-reviewer`, user confirms API).

**Orchestrator rules:**

- Run **`code-explorer`** when the queue says so—often **once** after `SPEC`/`SLICE_MATRIX` exists (full map), or **again** before a risky slice if BA schedules it.
- For each **implementation** step (`backend-dev`, `frontend-dev`), spawn a Task whose **single objective** is **one slice `SX`**: pass **`SLICE_SPEC`** (narrow AC + scope + out-of-scope reminder from the matrix), plus **`CODE_MAP`** filtered or scoped to that slice when BA provides boundaries; **do not** paste the full multi-slice matrix as the **task body** for the implementer unless BA marks it read-only “out of scope.”
- After **each** implementation slice: append slice notes to Handoff, update **`.cursor/active/{feature-slug}/progress.md`**, then execute the **control point** from `AGENT_QUEUE` (e.g. mini-review, full `code-reviewer`, or “record only” before the next slice).
- **`code-reviewer`** may run **between slices** (gate), **after each slice**, or **once at the end** on the **combined** diff—follow **`AGENT_QUEUE`**. On `request changes`, return to the **same slice’s** implementation agent, merge notes, re-run the scheduled review until approve / approve with minor comments or accepted risk.

**Typical compact pattern (when BA does not override):**

| Phase | Agent | Notes |
|-------|--------|--------|
| A | `business-analyst` | `SPEC` + `SLICE_MATRIX` + `AGENT_QUEUE` |
| B | `code-explorer` | Global `CODE_MAP` for the feature (once), unless BA slices explorer per step |
| C | `backend-dev` | Repeat **per backend slice** with narrow `SLICE_SPEC` |
| D | `frontend-dev` | Repeat **per frontend slice** with narrow `SLICE_SPEC` |
| E | `code-reviewer` | Per BA queue: between slices and/or final pass on cumulative changes |

For **backend-only**: still **multiple** `backend-dev` Tasks—one per slice—not one Task for the entire TZ.

## Before anything else

1. Read **all** `*.md` files in `.cursor/agents/` once per orchestration so ordering respects each agent’s **inputs**, **outputs**, **stop conditions**, and **readonly** flag.
2. Align with **`.cursor/rules/feature-delivery-workflow.mdc`**: feature slug, `.cursor/features/{slug}/feature.md`, `.cursor/active/{slug}/`, `docs/features/{slug}.md`, action-log updates, **Docker-backed** backend tests when `backend/` changes, and **frontend** verification (`npm run lint` / `npm run build` in `frontend/`) when `frontend/` changes.

## Default pipeline (legacy linear view — expand by slices)

When no custom queue exists yet, use this **shape**; once **`AGENT_QUEUE`** is present, **replace** the middle with explicit slice steps.

| Step | Agent (`name` in frontmatter) | Cursor Task `subagent_type` | Depends on |
|------|-------------------------------|-----------------------------|------------|
| 1 | `business-analyst` | `business-analyst` | User feature + context; `docs/` as required by that agent file → delivers **`SPEC` + `SLICE_MATRIX` + `AGENT_QUEUE`** |
| 2 | `code-explorer` | `code-explorer` | `SPEC` (+ slices for scope); produces **`CODE_MAP`** |
| 3a | `backend-dev` | `backend-dev` | **One slice at a time:** `SLICE_SPEC` for `SX` + relevant **`CODE_MAP`** + prior notes; run **only** if this slice touches `backend/` |
| 3b | `frontend-dev` | `frontend-dev` | **One slice at a time:** same pattern for `frontend/` |
| 4 | `code-reviewer` | `code-reviewer` | Per queue: **TZ / acceptance criteria** + **`DIFF_OR_FILES`** for the slice or cumulative set under review |

**Ordering 3a vs 3b:** Prefer **`backend-dev` before `frontend-dev`** when the UI depends on new API behavior; parallel Tasks **only** when BA explicitly marks independent slices and contracts are stable.

**Loop:** If review **requests changes**, return to **`backend-dev`** / **`frontend-dev`** for the **affected slice(s)** only, update Handoff, then re-run the **scheduled** review step until verdict is acceptable.

## Handoff bundle (what to pass between agents)

Maintain one growing **Handoff** block in the parent session (or in `.cursor/active/{feature-slug}/progress.md`) so each Task receives everything it needs:

- **`USER_FEATURE`**: Original ask, links, feature slug, constraints.
- **`SPEC`**: Full output of `business-analyst` (whole-feature TZ). Do not drop numbered requirements.
- **`SLICE_MATRIX`** / **`AGENT_QUEUE`**: From `business-analyst`; orchestrator follows **`AGENT_QUEUE`** literally.
- **`ACTIVE_SLICE`**: e.g. `S2` — which slice this Task implements.
- **`SLICE_SPEC`**: Narrow spec for **`ACTIVE_SLICE`** only (copy from matrix + BA prompt template).
- **`CODE_MAP`**: From `code-explorer` (global or slice-scoped per BA).
- **`BACKEND_NOTES`**: Accumulated notes from **each** `backend-dev` slice: commands, pytest evidence, files touched (append per slice or tag by `SX`).
- **`FRONTEND_NOTES`**: Same for **`frontend-dev`** slices.
- **`DIFF_OR_FILES`**: What `code-reviewer` needs—`git diff` or paths + intent for the **scope under review** (one slice or full feature per gate).

**Rule:** Each Task prompt must include the **artifacts that agent’s file requires**. Implementation Tasks get **one slice objective** plus **`SLICE_SPEC`**, not an undifferentiated full matrix as the only instruction. If an agent’s file says to stop when an input is missing, **stop the pipeline** and ask the user once, concisely.

## Choosing order (not only the default)

After reading `.cursor/agents/*.md`, adjust:

- **Spec already frozen** (e.g. complete `feature.md` + acceptance criteria): skip `business-analyst` or narrow to “validate / produce slices only”; still ensure **`AGENT_QUEUE`** or equivalent slice list exists before multi-step implementation.
- **Read-only exploration**: only `code-explorer` (and optionally `business-analyst` for questions)—do not invoke `backend-dev` or `frontend-dev`.
- **Backend-only or frontend-only**: still use **multiple** Tasks of the single implementation agent **per slice** when `SLICE_MATRIX` has more than one row.
- **Emergency fix** with tiny blast radius: user may allow skipping `business-analyst`; use a **single-slice** implicit matrix; still run `code-reviewer` if production logic changed.
- **Agents marked `readonly: true`**: never use them to edit files; they only produce analysis.

If a **new** agent file appears in `.cursor/agents/`, merge it into the graph by reading its declared inputs/outputs—do not assume the default table is complete forever.

## Project adaptation (kino vs older agent copy)

Agent bodies may mention another product stack. For **this** repo, the orchestrator must **map** instructions to:

- Backend: **FastAPI**, services under `backend/`, tests under `backend/src/tests/`, run via **`Makefile` / Docker** (see `.cursor/tech.md`).
- Frontend: React + Telegram UI per **`.cursor/rules/frontend-react-telegram-ui-standards.mdc`**.
- Layering and services: **`.cursor/rules/backend-fastapi-standards.mdc`**.

When spawning `backend-dev`, **`frontend-dev`**, or `code-reviewer`, **state these mappings explicitly** in the Task prompt so work matches kino (FastAPI + React/Telegram UI), not legacy stack examples inside older agent text.

## Execution mechanics

1. **Plan**: Write the ordered list from **`AGENT_QUEUE`** (or derived slice list) before the first implementation Task—each bullet is one **slice** or one **review gate**.
2. **Run**: For each step, call the **Task** tool with `subagent_type` set to the agent’s `name` when the IDE exposes that type; `readonly: true` when the agent file is read-only; and a **single** prompt containing Handoff fields needed for **that** step. Implementation prompts = **one slice + `SLICE_SPEC`**. If `frontend-dev` (or another project agent) is **not** available as a Task type, follow the same prompt using **`.cursor/agents/{name}.md`** in the main agent without claiming a subagent run.
3. **Synthesize**: After each Task completes, append its deliverable to the Handoff and update `.cursor/active/{feature-slug}/progress.md`.
4. **Verify**: Do not claim completion without evidence (tests/lint) per **verification-before-completion** and workspace rules—**per slice** as work lands, and **once** for the feature if BA mandates a final gate.

## Stop conditions

- Missing access to linked systems (issue tracker, Figma, etc.): pause and ask the user once.
- Unresolved **blocking** open questions from `business-analyst`: do not start `backend-dev` or `frontend-dev`.
- **`AGENT_QUEUE` / `SLICE_MATRIX` missing** when the feature is non-trivial: run `business-analyst` first or ask the user for an explicit slice breakdown—avoid one giant implementation Task.
- If `code-explorer` returns empty or conflicting mapping: narrow the question with the user or rescope the feature before coding.

## Optional deep reference

For long examples of Handoff prompts, see [reference.md](reference.md); extend templates there with **`SLICE_SPEC`** / **`ACTIVE_SLICE`** placeholders when prompting implementers. Otherwise keep prompts in `progress.md` fragments under `.cursor/active/{feature-slug}/`.
