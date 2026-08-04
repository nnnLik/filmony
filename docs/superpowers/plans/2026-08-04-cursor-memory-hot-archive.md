# Cursor Memory Hot Archive Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> Spec source of truth: [docs/superpowers/specs/2026-08-04-cursor-memory-hot-archive-design.md](docs/superpowers/specs/2026-08-04-cursor-memory-hot-archive-design.md) · Feature: [.cursor/features/cursor-memory-hot-archive/feature.md](.cursor/features/cursor-memory-hot-archive/feature.md)

**Goal:** Bound agent session memory to ~1–5 KB via `.cursor/HOT.md`, archive eviction policy, and trimmed action-log index — without losing historical delivery artifacts.

**Architecture:** HOT is the sole session entrypoint listing ≤1 in_progress slug(s) and exactly 3 recent_completed. Phase A sets policy only; Phase B moves evicted folders to `.cursor/archive/`; Phase C simplifies workflow and retires stale indexes. Product truth stays in `docs/features/{slug}.md`.

**Tech Stack:** Markdown meta only (`.cursor/` rules, README, HOT, logs) — no product code changes.

## Global Constraints

- **No product code changes** in any phase.
- **Archive ban:** agents must not read/glob `.cursor/archive/**` unless user explicitly requests recovery.
- **Slug-directed reads:** deep-read `active/`, `memory/logs/`, `plans/` only for HOT-listed slugs or user-named slugs.
- **Hot cardinality:** `len(in_progress) ≤ 1` (convention; may list 2 during this feature rollout). `len(recent_completed) = 3` in steady state.
- **Never move/delete:** `docs/features/**`, `.cursor/features/**`.
- **Phase B:** leave `.cursor/features/index.yaml` unchanged (Phase C deletes it).
- **Docker-first backend rules** unchanged.
- Delivery artifacts: `.cursor/active/cursor-memory-hot-archive/{plan,progress,result}.md`, `docs/features/cursor-memory-hot-archive.md`, milestone action-log fragments.

---

## Phase A — Policy and HOT (tokens; no mass move)

**Objective:** New sessions load HOT only; stop context bleed from historical `active/` and logs.

### Task A1 — Create HOT.md

- [x] Create `.cursor/HOT.md` from design spec seed
- [x] Include `cursor-memory-hot-archive` in `in_progress` alongside `unlimited-watch-note`
- [x] List top 3 `recent_completed` by closeout date (profile-gamification-stamps, director-catalog-pages, catalog-community-page)

**Verify:** File exists; agent read policy preamble present; 2 in_progress + 3 recent.

### Task A2 — Update feature-delivery-workflow.mdc

- [x] Add session start: read `.cursor/HOT.md` first
- [x] Add archive ban and slug-directed read rules after Mandatory Folder Structure
- [x] Add hot window policy (3 recent_completed; eviction on closeout)
- [x] Redefine action-log: one fragment per milestone or closeout; index ≤25 links
- [x] Preserve existing lifecycle steps; align step 6 logging with milestone/closeout
- [x] Keep `alwaysApply: true` frontmatter

**Verify:** Rule file valid frontmatter; HOT-first visible near top.

### Task A3 — Update .cursor/README.md

- [x] Add Step 0: read `.cursor/HOT.md` before any active/log glob
- [x] Document closeout: update HOT → append closeout fragment → trim action-log index
- [x] Link HOT as canonical feature registry (until Phase C deletes index.yaml)

**Verify:** README flow starts with HOT.

### Task A4 — Trim action-log.md index

- [x] Keep header and schema
- [x] Reduce Latest Entries to ≤25 newest fragment links
- [x] Prefer HOT-related slugs + newest overall
- [x] Do not delete fragment files on disk

**Verify:** Count fragment links in Latest Entries ≤ 25.

### Task A5 — Feature delivery scaffold

- [x] Create `.cursor/features/cursor-memory-hot-archive/feature.md`
- [x] Create `.cursor/active/cursor-memory-hot-archive/plan.md` (A/B/C checkboxes)
- [x] Create `.cursor/active/cursor-memory-hot-archive/progress.md` (Phase A log)

**Verify:** All artifacts exist; Phase A checkboxes marked done.

---

## Phase B — Hygiene (mass move)

**Objective:** Disk layout matches architecture; hot directories contain only HOT-listed slugs.

### Task B1 — Inventory evicted slugs

- [ ] Run `find .cursor/active -name result.md` and diff against HOT slugs
- [ ] Produce documented `mv` list (~54 slugs per design spec)
- [ ] Note `# queued_for_archive: {slug}` evictions from HOT footer if any

**Verify:** List covers all completed active folders not in HOT.

### Task B2 — Archive active workspaces

- [ ] Create `.cursor/archive/active/` if missing
- [ ] Move each evicted `.cursor/active/{slug}/` → `.cursor/archive/active/{slug}/`
- [ ] Leave HOT-listed slugs in place

**Verify:** `find .cursor/active -name result.md | wc -l` ≤ 4.

### Task B3 — Archive log fragments

- [ ] Move fragments not linked from hot `action-log.md` → `.cursor/archive/logs/`
- [ ] Optional: monthly rollups if >10 fragments per archived month

**Verify:** Hot tree retains only indexed fragments; index still ≤25 links.

### Task B4 — Archive plans and meta folders

- [ ] Move superseded `.cursor/plans/*` → `.cursor/archive/plans/`
- [ ] Move meta folders (`session-rollup-*`, `product-ideas-*`) → `.cursor/archive/active/`
- [ ] Confirm `index.yaml` unchanged

**Verify:** `plans/` contains only open/hot plans.

---

## Phase C — Workflow simplify

**Objective:** Reduce mandatory micro-artifacts; fix meta conflicts; retire stale indexes.

### Task C1 — Logging alignment

- [ ] Update rules to milestone/closeout-only (remove micro-action requirement from step 3/progress)
- [ ] Audit `memory/features/` — keep cross-cutting only

**Verify:** Rules no longer require per-action fragments.

### Task C2 — Retire index.yaml

- [ ] Delete `.cursor/features/index.yaml`
- [ ] Document HOT as canonical registry in `.cursor/README.md`

**Verify:** No stale registry file; HOT referenced as SoT.

### Task C3 — Archive orphans and legacy

- [ ] Archive `product-ideas-2026-07`, `session-rollup-*` under `archive/active/`
- [ ] Move superseded `webtorrent` plan to `archive/plans/`
- [ ] Archive `.cursor/active/001`–`009` if present (verify contents first)

**Verify:** Orphans not in hot `active/` tree.

### Task C4 — Orchestration conflict

- [ ] Keep `feature-delivery-workflow.mdc` as lifecycle SoT
- [ ] Limit `composer-token-economy-orchestrator` to mechanical delegation
- [ ] Document `feature-agent-pipeline` as optional in `.cursor/agents/README.md`

**Verify:** No duplicate lifecycle steps in always-applied rules.

### Task C5 — docs/ai/README.md stub

- [ ] Create stub pointing to `docs/README.md` and HOT-first workflow

**Verify:** File exists; linked agents can resolve reference.

### Task C6 — Closeout

- [ ] Write `result.md` and `docs/features/cursor-memory-hot-archive.md`
- [ ] Update HOT (move slug to recent_completed or remove if fully done)
- [ ] Append one closeout action-log fragment

**Verify:** Feature complete per workflow rules.

---

## Success metrics

| Metric | Before | After A | After B | After C |
|--------|--------|---------|---------|---------|
| Default `.cursor/` read | ~100–500+ KB | ~1–5 KB | ~1–5 KB | ~1–5 KB |
| `active/` with `result.md` | ~58 | ~58 | ≤4 | ≤4 |
| Hot log index links | ~200 | ≤25 | ≤25 | ≤25 |
| Stale `index.yaml` | Yes | Yes | Yes | Deleted |
