# cursor-memory-hot-archive

**Status:** in_progress  
**Date:** 2026-08-04  
**Spec:** `docs/superpowers/specs/2026-08-04-cursor-memory-hot-archive-design.md`

## Problem

The `.cursor/` workspace has grown into a high-token surface (~63 active folders, ~228 log fragments). Agents load hundreds of KB on every cold session. There is no eviction policy; completed delivery artifacts never leave the hot tree.

## Scope

### Phase A — Policy and HOT (no mass move)

- Create `.cursor/HOT.md` as session entrypoint (~1–2 KB).
- Update `feature-delivery-workflow.mdc` and `.cursor/README.md` with HOT-first rules, archive ban, slug-directed reads, milestone/closeout logging.
- Trim `action-log.md` index to ≤25 fragment links.
- Document closeout procedure: update HOT → append one closeout fragment → trim index.

### Phase B — Hygiene (mass move)

- Move completed `active/{slug}/` not in HOT → `archive/active/{slug}/`.
- Archive non-hot log fragments and superseded plans.
- Leave `.cursor/features/index.yaml` unchanged.

### Phase C — Workflow simplify

- Align rules with milestone-only logging.
- Trim `memory/features/` to cross-cutting notes only.
- Delete `index.yaml`; HOT becomes canonical registry.
- Resolve composer vs pipeline orchestration conflict.
- Create `docs/ai/README.md` stub.

## Acceptance criteria

### Phase A

- [x] `.cursor/HOT.md` exists with seed content (2 in_progress + 3 recent_completed).
- [x] `feature-delivery-workflow.mdc` mandates HOT-first session start, archive ban, hot window, ≤25 log index.
- [x] `.cursor/README.md` documents Step 0 (read HOT) and closeout → update HOT.
- [x] `action-log.md` indexes ≤25 newest fragment links; fragment files on disk unchanged.
- [x] Feature delivery artifacts exist under `.cursor/features/` and `.cursor/active/`.

### Phase B

- [ ] `find .cursor/active -name result.md | wc -l` ≤ 4.
- [ ] Evicted slugs live under `.cursor/archive/active/`.
- [ ] Non-hot log fragments moved to `.cursor/archive/logs/`.

### Phase C

- [ ] `index.yaml` deleted; HOT documented as canonical registry.
- [ ] Single unambiguous lifecycle in always-applied rules.
- [ ] `docs/ai/README.md` stub exists.

## Non-goals

- Product code changes.
- Git history rewriting.
- Automating HOT updates via hooks (manual closeout acceptable for A–B).
