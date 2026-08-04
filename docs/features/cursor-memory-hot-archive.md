# Cursor memory hot archive

Bounded `.cursor/` session memory: agents read **HOT.md** first instead of scanning all of `active/` and `memory/logs/`.

## Problem

Cold agent sessions previously loaded hundreds of KB from ~63 active folders and ~228 log fragments. Completed delivery artifacts never left the hot tree.

## Solution

Three phases (A → B → C):

1. **Phase A — Policy:** `.cursor/HOT.md` entrypoint; HOT-first rules in `feature-delivery-workflow.mdc`; milestone/closeout logging; ≤25 action-log index links.
2. **Phase B — Hygiene:** Move evicted `active/`, log fragments, and superseded plans to `.cursor/archive/`; hot tree holds HOT-listed slugs only.
3. **Phase C — Simplify:** Delete stale `index.yaml`; HOT = canonical hot-window registry; delegation-only composer skill; optional agent pipeline; `docs/ai/README.md` stub.

## Agent policy

| Allowed at session start | Forbidden without HOT slug or user name |
|--------------------------|----------------------------------------|
| `.cursor/HOT.md` | Glob/list all of `.cursor/active/` |
| Always-applied rules | Glob/list all of `.cursor/memory/logs/` |
| HOT-listed slug paths | Read/glob `.cursor/archive/**` |

**Product truth:** prefer `docs/features/{slug}.md` for shipped behavior.

## Hot window

- At most one `in_progress` slug (convention).
- Exactly **three** `recent_completed` slugs after each closeout (re-sort by closeout date, evict fourth to archive).

## Source-of-truth hierarchy

1. Product: `docs/features/{slug}.md`
2. Scope: `.cursor/features/{slug}/feature.md`
3. Delivery (hot): `.cursor/active/{slug}/`
4. Cross-cutting notes: `.cursor/memory/features/` (sparse)
5. Historical: `.cursor/archive/` (agents do not load)

## Orchestration

- **Lifecycle:** `feature-delivery-workflow.mdc` + `.cursor/README.md`
- **Mechanical delegation:** `composer-token-economy-orchestrator` → `composer-common-agent`
- **Optional multi-agent:** `feature-agent-pipeline` skill + `.cursor/agents/`

## References

- Design spec: `docs/superpowers/specs/2026-08-04-cursor-memory-hot-archive-design.md`
- HOT: `.cursor/HOT.md`
- AI stub: `docs/ai/README.md`
