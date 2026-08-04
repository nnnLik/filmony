# cursor-memory-hot-archive — active plan

**Status:** done  
**Phase:** A complete; B complete; C complete; closeout complete
**Spec:** `docs/superpowers/specs/2026-08-04-cursor-memory-hot-archive-design.md`  
**Implementation plan:** `docs/superpowers/plans/2026-08-04-cursor-memory-hot-archive.md`

## Phase A — Policy and HOT

- [x] Publish design spec
- [x] Create `.cursor/HOT.md` with seed (cursor-memory-hot-archive + unlimited-watch-note + 3 recent)
- [x] Patch `feature-delivery-workflow.mdc` (HOT-first, archive ban, log policy)
- [x] Patch `.cursor/README.md` (Step 0: read HOT; closeout procedure)
- [x] Trim `action-log.md` index to ≤25 fragment links
- [x] Create feature delivery artifacts (this folder + `feature.md`)

## Phase B — Hygiene (mass move)

- [x] Document or script `mv` list for ~54 evicted `active/` slugs
- [x] Move completed `active/{slug}/` not in HOT → `archive/active/{slug}/`
- [x] Archive log fragments not in hot index → `archive/logs/`
- [x] Archive superseded `.cursor/plans/*` → `archive/plans/`
- [x] Move meta/non-feature folders from `active/` → `archive/active/`
- [x] Confirm `index.yaml` left unchanged

## Phase C — Workflow simplify

- [x] Align rules: mandatory micro-log → milestone/closeout only
- [x] Trim `memory/features/` to cross-cutting notes only (2 files retained)
- [x] Delete `index.yaml`; document HOT as canonical registry in README
- [x] Archive legacy meta folders and orphans (Phase B; webtorrent plan in archive/plans)
- [x] Resolve orchestration conflict (workflow SoT + delegation-only composer)
- [x] Create `docs/ai/README.md` stub
