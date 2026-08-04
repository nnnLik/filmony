# cursor-memory-hot-archive — result

**Status:** done  
**Closed:** 2026-08-04T120000Z

## What shipped

### Phase A — Policy and HOT
- Created `.cursor/HOT.md` as session entrypoint.
- Updated `feature-delivery-workflow.mdc`: HOT-first, archive ban, slug-directed reads, milestone/closeout logging, ≤25 action-log index.
- Updated `.cursor/README.md` with Step 0 (read HOT) and closeout procedure.

### Phase B — Hygiene
- Created `.cursor/archive/{active,logs,plans}/`.
- Moved **66** completed/non-HOT `active/{slug}/` dirs → `archive/active/`.
- Moved **207** log fragments not in hot index → `archive/logs/` (kept **25** indexed fragments + `action-log.md`).
- Moved **13** superseded plans → `archive/plans/`; added `rollup-2026-05.md`.

### Phase C — Workflow simplify
- Deleted `.cursor/features/index.yaml`; HOT is the canonical hot-window registry.
- Created `.cursor/agents/README.md` (optional pipeline; lifecycle SoT = `feature-delivery-workflow.mdc`).
- Created `docs/ai/README.md` stub.
- Scoped `composer-token-economy-orchestrator` to delegation-only (no lifecycle duplication).
- Marked `feature-agent-pipeline` skill as optional / not always-applied.
- Updated `.cursor/features/README.md` to point at HOT.
- Confirmed `webtorrent` plan under `.cursor/archive/plans/`.
- Evicted `catalog-community-page` from HOT → `archive/active/catalog-community-page/`.
- `memory/features/` retained cross-cutting notes only (2 files).

## Verification (post-closeout)

| Metric | Count |
|--------|------:|
| `.cursor/active/` dirs (excl. `README.md`) | 5 |
| HOT slugs in active | 4 + `templates` |
| Hot log files (`action-log.md` + fragments) | 26 |
| Archived active dirs | 67 |
| Archived log fragments | 207 |
| Archived plans | 13 |
| `index.yaml` | deleted |

Commands used:
```bash
ls -1 .cursor/active/ | wc -l          # 6 (5 dirs + README.md)
ls -1 .cursor/archive/active/ | wc -l # 67
ls .cursor/memory/logs/*.md | wc -l   # 26
test ! -f .cursor/features/index.yaml
```

## Limitations / next steps

- HOT updates remain manual on closeout (no automation hook).
- `unlimited-watch-note` stays in_progress until pytest verification and closeout.
- Historical fragments under `archive/logs/` are human-recovery only; agents must not read `archive/**` unless user asks.
