# Catalog / cards: v2 API & naming cleanup map (film-era legacy removal)

This document is a **roadmap** for safely retiring **wire and persistence names** that still say `movie_card*` / `referenced_movie_*` while the domain model is **card-first** (`UserCard`, catalog-linked film/game/manual). It complements the shipped catalog search work documented in [`catalog-search-providers.md`](catalog-search-providers.md).

**Scope note:** `film_id` on `catalog_item`, `user_card` (table `movie_card`), and watchlist/film community routes are **real domain fields** for the **Film** entity. They are **not** automatically “legacy” the way `movie_card_id` JSON keys are. This map calls out where **`film_*` must stay** vs where **`film_*` on API payloads is only historical naming**.

---

## Goals

- **Single public vocabulary** for HTTP/Telegram clients: `user_card`, `user_card_id`, `referenced_user_cards`, reaction `target_kind` values aligned with domain (`user_card` / `user_card_comment`), without breaking active clients mid-flight.
- **Safer internal ergonomics**: Python symbols and file names already trend card-first; finish stragglers where they do not touch wire.
- **Explicit DB migration chapter**: table `movie_card` → `user_card` (and friends) is a **late, optional** phase with its own rollback story.

Non-goals for the **first** phases: renaming the `film` table, removing Kinopoisk IDs, or changing `catalog_item.film_id` / `game_id` XOR semantics.

---

## Inventory — legacy surface (exact areas)

### Persistence (must phase — breaking DDL / FK names)

| Artifact | Current | Target (conceptual) | Risk |
|----------|---------|---------------------|------|
| ORM `UserCard` | `__tablename__ = 'movie_card'` | `user_card` (via migration + rename) | **High** — FKs, indexes, downtime strategy |
| Comments table | `movie_card_comment`, column `movie_card_id` | `user_card_comment`, `user_card_id` | **High** |
| Index / constraint names | `ix_movie_card_*`, `uq_movie_card_*`, partial uniques | renamed to `user_card_*` | Medium (mostly operational noise unless ORM expects names) |
| Media keys / prefixes | `user_media/movie_card_comments/` | `user_media/user_card_comments/` (or generic `card_comments`) | Medium — blob store + URL compatibility |

### Wire — HTTP JSON (must phase — client contract)

Representative patterns (not exhaustive grep; extend during Phase 0 audit):

| Area | Legacy keys / literals | Files / notes |
|------|-------------------------|---------------|
| Cards | `movie_card_id`, `referenced_movie_cards`, `referenced_movie_card_id`, feed item `kind: 'movie_card'` | `backend/src/api/cards/schemas.py`, `feed/routes.py`, `feed_posts/schemas.py` |
| Profile / lists | `film_id` on list items where it means “linked film row” (may stay as domain field); **counts** like `movie_cards` / `movie_cards_count` | `backend/src/api/profile/schemas.py`, `backend/src/api/search/schemas.py` |
| Feed compose | `referenced_movie_card_id` (with alias `referenced_card_id` already — good bridge) | `feed_posts/schemas.py` |
| Reactions API | `target_kind: 'movie_card' \| 'movie_card_comment'` | `ReactionTargetKind` stores these strings today (`backend/src/models/reaction_target_kind.py`) |
| Routes (paths) | `/watchlist/films/{film_id}` | Film watchlist is domain-correct; **optional** later alias `/watchlist/movies/...` only if product wants URL consistency |

### Workers / tasks (must phase — Celery registry)

- `tasks.telegram_engagement.deliver_shared_movie_card`
- `tasks.telegram_engagement.notify_movie_card_*` (root comment, mentions, etc.)

Callers in `backend/src/api/cards/routes.py` (and any engagement package) must move to **new task names** with a **dual-registration or bridge period**.

### Frontend (must phase in lockstep with API)

Types and usage mirror backend: `movie_card_id`, `referenced_movie_cards`, `movie_cards_count`, `targetKind: 'movie_card'`, helpers like `movieCardRefTokenFromId`, pages named `MovieCardDetailPage`. Plan client releases **after** additive API fields land.

### Can rename now (internal-only — no wire/DB)

When a change **does not** alter serialized JSON, Celery task **names** registered in workers, DB identifiers, or stored blob prefixes:

- **Python modules / private helpers** already partially migrated (`create_user_card.py`, etc.); remaining **route handler names** `get_my_movie_card_*`, test file names `test_movie_card_*` — safe renames with test updates.
- **Comments in code** referring to “movie card” where they mean user card.
- **Internal DTO field names** not exposed on HTTP (verify with contract tests before merge).

**Caution:** renaming **public** Python symbols that generate OpenAPI (`Field` names without aliases) **does** change wire — treat as API phase.

---

## Phased rollout

### Phase 0 — Inventory, telemetry, migration gates (no behavior change)

- **Contract snapshot:** export OpenAPI or generate golden JSON fixtures for feed, cards, reactions, profile list, search suggestion payloads.
- **Telemetry / logging (recommended):** behind settings, log counts of responses that still emit legacy keys (baseline). Optionally add `Sunset` / deprecation headers only after Phase 1 ships.
- **Migration gates (CI):**
  - pytest suites: `test_cards_routes`, `test_feed_*`, `test_reactions_*`, `test_engagement_telegram_notifications`, frontend `npm run build` + typecheck.
  - **Backward-compat tests:** once Phase 1 adds parallel keys, tests assert **both** shapes until Phase 3.

### Phase 1 — Additive “v2” fields (safe default)

**Principle:** New keys **alongside** old keys for one or more release trains.

| Legacy | Additive v2 (example) |
|--------|------------------------|
| `movie_card_id` | `user_card_id` (same int) |
| `referenced_movie_cards` | `referenced_user_cards` (same array shape) |
| `referenced_movie_card_id` | `referenced_user_card_id` (keep `referenced_card_id` alias if useful) |
| `movie_cards_count` (search/profile) | `user_cards_count` |
| Feed `kind: 'movie_card'` | add `kind: 'user_card'` **or** introduce `card_type` while accepting legacy `kind` on input |

**Reactions:** add **new** allowed `target_kind` strings (`user_card`, `user_card_comment`) in API validation **while still accepting** `movie_card*`. Persistence strategy:

- **Preferred:** store **canonical** new values in DB via migration + backfill + check constraint; **or**
- **Interim:** normalize at service boundary (read path maps old→new for clients, write path accepts both).

Document the chosen rule in `ReactionTargetKind` and enforce in `SetOrToggleUserReactionService`.

**Duration:** minimum **2 client release cycles** (Telegram WebApp cache + store delays), or **4–8 weeks** wall-clock for a small team — adjust per distribution.

### Phase 2 — Client + worker adoption

- Frontend: read v2 keys first, fall back to legacy; then switch writes to v2.
- **Celery:** deploy workers that register **new** task names; producers send **new** names; keep old task stubs that delegate to shared implementation for one deploy window.
- **Telegram bots / deep links:** audit message payloads for hard-coded “movie card” English or legacy task names.

**Gate:** error budget / no spike in reaction 4xx, feed publish failures, or notification drops.

### Phase 3 — Deprecation window (legacy read-only or warnings)

- API: stop **documenting** legacy keys in public docs; optionally omit legacy keys on **new** API version prefix (`/api/v2/...`) if you introduce URL versioning; otherwise use **time-based** removal after `Sunset` notices.
- Remove dual-write; keep dual-read **only** if needed for stale clients.

### Phase 4 — Breaking cleanup (major version or coordinated bump)

- Remove `movie_card_id`, `referenced_movie_cards`, etc. from JSON.
- **DB rename:** `movie_card` → `user_card`, `movie_card_comment` → `user_card_comment`, FK columns, indexes, Alembic batch + compatibility views **or** expand/contract migration pattern.
- Blob prefix migration: copy or rewrite `movie_card_comments` keys (background job + dual-prefix read fallback).

### Phase 5 — Optional URL and resource naming

- Film watchlist paths may remain film-specific (`/films/`).
- Card routes today use `/cards/{id}` — already neutral; keep.

---

## Removal order (recommended)

1. **Internal-only renames** (tests, handler names, non-serialized code) — lowest risk, no coordination.
2. **Additive API fields + reaction target_kind duality** — unlocks clients.
3. **Frontend + workers** switch to canonical keys / task names.
4. **Stop emitting legacy JSON** (API major).
5. **DB + blob renames** last — longest rollback, needs backups and rehearse.

---

## Rollback strategy

- **Phase 1–2:** feature flag `EMIT_LEGACY_CARD_WIRE=1` to re-include old keys if clients regress; workers keep old Celery task names as aliases.
- **Phase 4 DB:** restore from snapshot; or forward-only Alembic `downgrade` only if migrations were designed reversible (often **not** for renames — prefer **rehearsal** on staging + backup).
- **Blobs:** keep old prefix readable until TTL / migration job completes.

---

## Verification checklist (per phase)

| Phase | Verify |
|-------|--------|
| 0 | OpenAPI/golden JSON diff documented; baseline metrics |
| 1 | pytest + contract tests for **dual keys**; reaction toggle accepts both kinds |
| 2 | E2E: create card, comment, react, feed post with reference; Telegram notification smoke |
| 3 | Staging clients on v2 only; monitor 4xx |
| 4 | Full pytest, frontend build, load test on feed; DB migration dry-run |

---

## References

- Feature doc: [`catalog-search-providers.md`](catalog-search-providers.md)
- Active result log: `.cursor/active/catalog-search-providers/result.md`
- Universal cards: [`abstract-user-cards.md`](abstract-user-cards.md)
- Reaction storage note: `backend/src/models/reaction_target_kind.py` (enum members vs string values)

---

## Summary

**Rename now** when it does not cross HTTP, Celery task registry, DB identifiers, or blob paths. **Phase everything else:** additive fields first, migrate clients and workers, then drop legacy keys and finally consider physical table renames. **`film_id` where it denotes the Film row remains**; **`movie_card_*` JSON and table names** are the primary cleanup targets for a true “v2” public API.
