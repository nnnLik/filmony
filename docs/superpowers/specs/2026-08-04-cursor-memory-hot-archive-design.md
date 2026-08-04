# Cursor memory optimization — Hot-pointer + archive

**Status:** approved  
**Date:** 2026-08-04  
**Approach:** 1 — Hot-pointer + archive (`N = 3` recent completed)  
**Phases:** A → B → C (sequential; each phase shippable independently; **one `plan.md` per phase** — this file is the umbrella design, not a single implementation plan)

---

## Problem

The `.cursor/` workspace has grown into a high-token surface that agents load on every session:

| Area | Observed scale (2026-08-04 inventory) | Agent impact |
|------|----------------------------------------|--------------|
| `.cursor/active/` | ~63 folders; ~58 with `result.md` (completed) | Glob/list pulls hundreds of KB of plan/progress/result markdown |
| `.cursor/memory/logs/` | ~228 fragment files + index | Action-log index and fragments dominate context |
| `.cursor/plans/` | 14 plan files | Mixed hot and superseded plans |
| `.cursor/features/index.yaml` | 8 entries; stale vs repo | Misleading registry; conflicts with always-on rules |
| Rule overlap | `composer-token-economy-orchestrator` vs `feature-agent-pipeline` | Agents receive conflicting orchestration guidance |

Current rules (`feature-delivery-workflow.mdc`, `.cursor/README.md`) require agents to treat **all** of `active/`, **all** log fragments, and optional feature memory as live working set. There is no eviction policy. Product truth already lives in `docs/features/{slug}.md`, but delivery artifacts never leave the hot tree.

**Symptom:** A cold session routinely ingests hundreds of KB from `.cursor/` before touching product code. Most of that data is historical and irrelevant to the current task.

---

## Goals

1. **Bounded session memory:** New agent sessions load ~1–2 KB from `.cursor/HOT.md` instead of scanning `active/` and `memory/logs/`.
2. **Explicit hot set:** At most one `in_progress` slug (can be zero) plus exactly **three** `recent_completed` slugs in HOT after each closeout update (steady state; closeout atomically evicts a fourth completion in the same edit).
3. **Archive without loss:** Completed work outside the hot window moves to `.cursor/archive/`; product docs and feature specs stay put.
4. **Agent-safe boundaries:** Rules forbid glob/read of `.cursor/archive/**` and bulk scans of `active/` or `memory/logs/` unless the slug is listed in HOT (or the user names a slug explicitly).
5. **Phased rollout:** Phase A delivers token savings and policy without mass file moves; Phase B performs hygiene; Phase C simplifies workflow and resolves meta conflicts.

---

## Constraints

- **Product source of truth:** `docs/features/{slug}.md` — never archived, never deleted by this initiative.
- **Feature specs:** `.cursor/features/{slug}/feature.md` — permanent; not moved to archive.
- **Hot cardinality:** `len(in_progress) ≤ 1` (practical convention; HOT may list zero in-progress slugs between features). `len(recent_completed) = 3` always once HOT is seeded (Phase A day 1); each closeout re-sorts and trims to three in the same HOT edit.
- **Archive ban:** Agents must not read, glob, or grep `.cursor/archive/**` unless the user explicitly requests historical recovery.
- **Slug-directed reads:** Deep reads of `.cursor/active/{slug}/`, `.cursor/memory/logs/*{slug}*`, and `.cursor/plans/*{slug}*` require the slug to appear in HOT or be user-named.
- **No product code changes** in any phase of this initiative.
- **Docker-first backend rules** unchanged; this spec only touches `.cursor/` meta and agent rules/docs.

---

## Architecture

### HOT.md — thin session memory

Path: **`.cursor/HOT.md`**

HOT is the **only** `.cursor/` file agents should load at session start (plus always-applied rules that reference it). It is hand-maintained on closeout and updated when starting or finishing a feature.

**Sections (fixed order):**

```markdown
# HOT — Cursor session memory
Updated: YYYY-MM-DD

## in_progress
- `{slug}` — links

## recent_completed
1. `{slug}` — closed YYYY-MM-DDTHHMMSSZ — links
2. ...
3. ...
```

**Per-slug link block (required for every HOT entry):**

| Link | Path |
|------|------|
| Feature spec | `.cursor/features/{slug}/feature.md` |
| Delivery workspace | `.cursor/active/{slug}/` |
| Product doc | `docs/features/{slug}.md` |

Optional fourth line when a durable cross-cutting note exists: `.cursor/memory/features/{slug}.md`.

### Closeout date rule

**Closeout date** = timestamp of the **docs/closeout** action-log fragment for the slug (filename prefix `YYYY-MM-DDTHHMMSSZ-{slug}-*.md` indexed in `action-log.md`). If no closeout fragment exists, use the latest fragment timestamp for that slug; if none, use `result.md` mtime (ISO date).

**Eviction:** When a fourth feature completes, append it to `recent_completed`, re-sort by closeout date descending, keep top 3, remove the evicted slug from HOT and queue it for Phase B archive (Phase A: note evicted slug in HOT footer comment `# queued_for_archive: {slug}` until Phase B runs).

**Tiebreaker** (same closeout second): lexicographic slug ascending.

### Agent read policy

| Allowed at session start | Forbidden without slug from HOT or user |
|--------------------------|----------------------------------------|
| `.cursor/HOT.md` | Glob/list entire `.cursor/active/` |
| Always-applied rules | Glob/list entire `.cursor/memory/logs/` |
| User-named slug paths | Read/glob `.cursor/archive/**` |
| HOT-listed slug paths | Scan `.cursor/plans/` without slug filter |

**Product lookup:** For behavior questions about a shipped feature, prefer `docs/features/{slug}.md`. Use `active/{slug}/` only for in-flight or very recent delivery context.

### Source-of-truth hierarchy

1. **Product:** `docs/features/{slug}.md`
2. **Scope / acceptance:** `.cursor/features/{slug}/feature.md`
3. **Delivery (hot only):** `.cursor/active/{slug}/` — plan, progress, result while in HOT
4. **Cross-cutting durable notes:** `.cursor/memory/features/{slug}.md` — only when the note applies beyond one feature (Phase C tightens this)
5. **Historical delivery:** `.cursor/archive/active/{slug}/` — human recovery only; agents do not load

---

## Directory layout

### Target tree (after Phase B)

```
.cursor/
├── HOT.md                          # session entrypoint (~1–2 KB)
├── README.md                       # HOT-first workflow (Phase A)
├── features/
│   └── {slug}/feature.md           # permanent specs (never archived)
├── active/
│   └── {slug}/                     # in_progress + top-3 recent_completed only
├── memory/
│   ├── features/                   # durable cross-cutting notes only (Phase C)
│   └── logs/
│       ├── action-log.md           # hot index: ≤25 fragment links (HOT slugs + recent closeouts)
│       └── YYYY-MM-DDTHHMMSSZ-*.md # hot fragments only (Phase A policy)
├── plans/                          # open / hot plans only
└── archive/                        # agents MUST NOT read
    ├── active/
    │   └── {slug}/                 # evicted completed workspaces
    ├── logs/
    │   └── *.md                    # rolled-up or evicted fragments
    └── plans/
        └── *.md                    # superseded plan files
```

### What moves in Phase B

| Source | Destination | Condition |
|--------|-------------|-----------|
| `.cursor/active/{slug}/` | `.cursor/archive/active/{slug}/` | `result.md` exists AND slug not in HOT |
| `.cursor/memory/logs/*.md` | `.cursor/archive/logs/` | Fragment not linked from hot `action-log.md` and older than hot window |
| `.cursor/plans/*.md` | `.cursor/archive/plans/` | Plan superseded or feature archived |
| Meta folders under `active/` (e.g. `session-rollup-*`, `product-ideas-*`) | `.cursor/archive/active/{name}/` | Not a product feature slug; no HOT entry |

**Never move:** `docs/features/**`, `.cursor/features/**`.

**Deferred to Phase C:** orphan cleanup (`product-ideas-2026-07`, `session-rollup-*`, superseded `webtorrent` plan), legacy numbered folders `001`–`009` if present (none in 2026-08-04 inventory).

---

## Phases

### Phase A — Policy and HOT (tokens; no mass move)

**Objective:** New sessions load HOT only; stop context bleed from historical `active/` and logs.

**Deliverables:**

1. Create `.cursor/HOT.md` with initial seed (see [Initial HOT seed](#initial-hot-seed)).
2. Update `.cursor/rules/feature-delivery-workflow.mdc`:
   - Add **HOT-first session start** (read HOT before any `active/` or log glob).
   - Add **archive ban** and slug-directed read rules.
   - Redefine action-log policy: **one fragment per milestone or feature closeout** (not every micro-action).
   - `action-log.md` indexes at most **25** fragment links: all HOT-listed slugs plus the newest closeout fragments for slugs outside HOT (older links become plain slug references without fragment paths until Phase B archive).
3. Update `.cursor/README.md` to mirror HOT-first flow and point to HOT.md as step 0.
4. Document closeout procedure: on feature complete → update HOT → append one closeout fragment → trim `action-log.md` index.

**Explicitly not in Phase A:** Moving existing `active/` folders; deleting `index.yaml`; resolving composer vs pipeline conflict.

**Success metrics:**

- Cold agent prompt + rules + HOT ≤ ~5 KB `.cursor/` payload vs hundreds of KB today.
- Every new closeout updates HOT and adds exactly one closeout log fragment.

---

### Phase B — Hygiene (mass move)

**Objective:** Disk layout matches architecture; hot directories contain only HOT-listed slugs.

**Deliverables:**

1. Move all completed `active/{slug}/` not in HOT → `archive/active/{slug}/`.
2. Move non-hot log fragments → `archive/logs/`; optional monthly rollups: if a calendar month still has **>10** archived fragments after the hot trim, merge them into `archive/logs/rollup-YYYY-MM.md`.
3. Move superseded `.cursor/plans/*` → `archive/plans/`.
4. Move meta/non-feature folders from `active/` → `archive/active/`.
5. **Leave `.cursor/features/index.yaml` unchanged** (still stale; canonical registry moves to HOT in Phase C).

**Success metrics:**

- `find .cursor/active -name result.md | wc -l` ≤ 4 (3 recent + 0–1 in progress).
- `action-log.md` fragment links ≤ 25; all others archived.
- No agent rule references paths under `archive/` as live inputs.

---

### Phase C — Workflow simplify

**Objective:** Reduce mandatory micro-artifacts; fix meta conflicts; retire stale indexes.

**Deliverables:**

1. **Logging:** Mandatory micro-log per action → milestone/closeout only (align rules with Phase A policy).
2. **`memory/features/`:** Keep only cross-cutting notes; per-feature notes folded into `docs/features/` or archived.
3. **`index.yaml`:** **Delete** `.cursor/features/index.yaml` and document HOT as the canonical feature registry in `.cursor/README.md`.
4. **Legacy folders:** Archive `.cursor/active/001`–`009` if present (none in 2026-08-04 inventory); confirm contents exist in archive or `docs/features/` before delete.
5. **Orphans:** Archive `product-ideas-2026-07` and `session-rollup-*` under `archive/active/`; move superseded `webtorrent` plan to `archive/plans/` (non-feature research artifact).
6. **Orchestration conflict (decided):** `feature-delivery-workflow.mdc` remains lifecycle source of truth. `composer-token-economy-orchestrator` stays always-applied but limited to mechanical delegation (no duplicate lifecycle steps). `feature-agent-pipeline` is optional multi-agent mode only — documented in `.cursor/agents/README.md`, not always-applied.
7. **`docs/ai/README.md`:** **Create** a short stub (referenced by `business-analyst.md` and `code-explorer.md` but missing today) pointing to `docs/README.md` and the HOT-first workflow.

**Success metrics:**

- Single unambiguous lifecycle in always-applied rules.
- `memory/features/` file count stable and justified.
- No stale registry file confusing agents.

---

## Non-goals

- Changing application/backend/frontend product code.
- Finishing or testing `unlimited-watch-note` pytest (remains in_progress in HOT until verified).
- Automating HOT updates via hooks (manual closeout update is acceptable for Phase A–B).
- Migrating `docs/features/` content into `.cursor/`.
- Git history rewriting or committing archived blobs outside normal commits.

---

## Success metrics (summary)

| Metric | Before | After Phase A | After Phase B |
|--------|--------|---------------|---------------|
| Default `.cursor/` read size | ~100–500+ KB | ~1–5 KB (HOT + rules) | ~1–5 KB |
| `active/` folders with `result.md` | ~58 | ~58 (unchanged) | ≤ 4 |
| Log fragments in hot tree | ~228 | ~228 (policy only) | ≤ 25 indexed |
| Agent archive violations | N/A | 0 (rule-enforced) | 0 |
| Stale `index.yaml` | Yes | Still stale | Deleted (HOT canonical) |

---

## Initial HOT seed

Verified against `action-log.md` closeout timestamps on 2026-08-04.

### in_progress

| Slug | Rationale |
|------|-----------|
| `unlimited-watch-note` | `result.md` status: in_progress — code complete; pytest not run |

### recent_completed (top 3 by closeout date)

| Rank | Slug | Closeout fragment | Notes |
|------|------|-------------------|-------|
| 1 | `profile-gamification-stamps` | `2026-08-04T104900Z-profile-gamification-stamps-docs.md` | Latest closeout in log |
| 2 | `director-catalog-pages` | `2026-08-04T024100Z-director-catalog-pages-code.md` | Second on Aug 4 |
| 3 | `catalog-community-page` | `2026-08-04T011600Z-catalog-community-page-code.md` | Third; beats `offline-feed-cache` (same timestamp) via slug tiebreaker |

**Not in top 3 (evicted when Phase B runs):** `offline-feed-cache` (closeout `2026-08-04T011600Z`, tiebreaker), `social-depth-pack` (closeout `2026-07-29`, older), and ~53 other completed slugs under `active/`.

### Seed HOT.md content (Phase A implementer copy-paste)

```markdown
# HOT — Cursor session memory
Updated: 2026-08-04

## in_progress
- `unlimited-watch-note`
  - Feature: `.cursor/features/unlimited-watch-note/feature.md`
  - Active: `.cursor/active/unlimited-watch-note/`
  - Docs: `docs/features/unlimited-watch-note.md` (pending closeout)

## recent_completed
1. `profile-gamification-stamps` — closed 2026-08-04T104900Z
   - Feature: `.cursor/features/profile-gamification-stamps/feature.md`
   - Active: `.cursor/active/profile-gamification-stamps/`
   - Docs: `docs/features/profile-gamification-stamps.md`
2. `director-catalog-pages` — closed 2026-08-04T024100Z
   - Feature: `.cursor/features/director-catalog-pages/feature.md`
   - Active: `.cursor/active/director-catalog-pages/`
   - Docs: `docs/features/director-catalog-pages.md`
3. `catalog-community-page` — closed 2026-08-04T011600Z
   - Feature: `.cursor/features/catalog-community-page/feature.md`
   - Active: `.cursor/active/catalog-community-page/`
   - Docs: `docs/features/catalog-community-page.md`
```

---

## Implementation checklist (for plan.md)

### Phase A
- [x] Publish `docs/superpowers/specs/2026-08-04-cursor-memory-hot-archive-design.md` (this file)
- [ ] Create `.cursor/HOT.md` from seed above
- [ ] Patch `feature-delivery-workflow.mdc` (HOT-first, archive ban, log policy)
- [ ] Patch `.cursor/README.md` (step 0: read HOT)
- [ ] Verify: new session agent instructions cite HOT only

### Phase B
- [ ] Script or documented `mv` list for ~54 evicted `active/` slugs
- [ ] Archive log fragments not in hot index
- [ ] Archive superseded plans
- [ ] Confirm `index.yaml` left unchanged (Phase C deletes it)

### Phase C
- [ ] Apply orchestration decision (workflow SoT + delegation-only composer + optional pipeline)
- [ ] Trim `memory/features/`
- [ ] Archive legacy meta folders and orphans (`product-ideas-2026-07`, `session-rollup-*`, `webtorrent` plan)
- [ ] Delete `index.yaml`; create `docs/ai/README.md` stub

---

## References

- Current workflow: `.cursor/README.md`, `.cursor/rules/feature-delivery-workflow.mdc`
- Stale registry: `.cursor/features/index.yaml` (8 entries vs ~63 active folders)
- Action log index: `.cursor/memory/logs/action-log.md`
- Prior spec format: `docs/superpowers/specs/2026-07-23-taste-quiz-guess-rating-design.md`
