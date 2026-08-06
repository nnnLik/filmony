# Achievements: rarity, profile pins

## Metadata
- Feature slug: `achievements-rarity-profile-pins`
- Status: `in_progress`
- Target area: fullstack
- Created at: 2026-08-07
- Depends on: `collections-core` (collection progress + 100% completion hook)

## Problem
Users who complete curated film collections (Letterboxd Top 500, Oscar seasons, etc.) have no durable recognition on Filmony. There is no way to see how rare a completion is among active raters, or to showcase select achievements on a public profile. Without sticky unlocks and periodic rarity refresh, badges would feel unreliable (revoked after deleting a rating) or meaningless (always “100% of users”).

## Goal
Introduce **collection-completion achievements** with **sticky unlocks**, **global rarity stats** (percent + holder count), and **profile pins** (limited slots) so users can display their rarest completions to others.

## Scope

### In scope
- **Achievement catalog** — one achievement per collection definition:
  - Static collections (e.g. Letterboxd Top 500) — membership frozen; achievement stable forever.
  - Seasonal Oscar collections — one achievement per season slug (e.g. `oscars-2026`, `oscars-2027`).
- **Unlock rule** — grant achievement when user reaches **100% collection progress** via `collections-core` completion hook (idempotent; no duplicate rows).
- **Sticky unlock** — once granted, **never revoked** if the user later deletes ratings or collection progress drops below 100%.
- **Rarity** — for each achievement, store and expose:
  - `holders_count` — users who have unlocked the achievement.
  - `rarity_percent` — `holders_count / eligible_users_count * 100`, rounded for display.
  - **Eligibility denominator:** users with **≥1 rated card** (`UserCard` with rating, not planned-only). Document and enforce consistently in rarity service and API copy.
- **Rarity refresh** — Celery periodic task recalculates all achievement rarity snapshots; crontab documented in task module docstring; scheduled on **external host crontab** (no Beat in-repo). Pattern: `backend/src/tasks/monthly_recap.py`; ops: `docs/features/celery-redis-workers.md`.
- **Profile pins** — authenticated user can pin **1–3** unlocked achievements; order persisted; visible on **own** profile management UI and **public** profile for other viewers.
- **API** — list achievements (catalog + user state), unlock is internal (hook-driven), pin/unpin/reorder endpoints, public profile payload includes pinned achievements with rarity.
- **Frontend** — achievements list UI (own profile), pin picker with slot limit, pinned strip/section on public profile.
- **Tests** — pytest for unlock hook, sticky behavior, rarity math, pin limits, public API; frontend lint/build for touched files.

### Out of scope
- Arbitrary non-collection achievements (manual grants, rating streaks, social badges) — note as future extension via same `Achievement` / `UserAchievement` tables.
- Leaderboards or ranked “top achievers” views.
- Real-time rarity on every unlock (batch/periodic recalc is sufficient for v1).
- Notifications on unlock (optional follow-up).

## Functional Requirements

### FR-1 — Achievement catalog
- System defines achievements linked 1:1 to collection slugs from `collections-core`.
- Each achievement has stable `slug`, display name, description, optional icon key, and `collection_slug` FK/reference.
- Seed/migrate catalog when collections are registered (Letterboxd Top 500, Oscar seasons).

### FR-2 — Unlock on 100% completion
- `collections-core` emits or calls a completion hook when a user’s collection progress reaches 100%.
- Hook runs `GrantCollectionAchievementService` (idempotent): insert `UserAchievement` if absent; set `unlocked_at`.
- Re-running hook for same user+collection is a no-op.

### FR-3 — Sticky unlock
- Deleting ratings or membership changes that lower progress **must not** delete `UserAchievement` rows.
- Progress UI may show &lt;100% again; badge remains in “unlocked” state.

### FR-4 — Rarity calculation
- Denominator: count of distinct users with ≥1 rated `UserCard`.
- Numerator: count of distinct users with `UserAchievement` for that achievement.
- Persist `holders_count`, `eligible_users_count`, `rarity_percent` on `Achievement` (or companion snapshot row) updated by periodic task.
- Expose rarity on achievement list and pinned profile payloads.

### FR-5 — Periodic rarity task
- Celery task module `backend/src/tasks/achievement_rarity.py` with `register_tasks(app)`.
- Module docstring documents recommended crontab (e.g. daily 03:00 UTC).
- Task calls `RecalculateAchievementRarityService` for all catalog achievements.
- Register in `celery_app._register_all_tasks`; ops schedule via external crontab per `docs/features/celery-redis-workers.md`.

### FR-6 — Profile pins
- User may pin **at most 3** unlocked achievements.
- Pin, unpin, and reorder via authenticated API.
- Attempting to pin locked achievement or exceed slot limit → 4xx with clear error.
- Public profile endpoint includes ordered pinned achievements (slug, title, rarity fields, unlocked_at).

### FR-7 — UI
- Own profile: section to browse unlocked/locked achievements, see rarity, manage pins.
- Public profile: read-only pinned achievements visible to any authenticated viewer (same visibility rules as public profile today).

## Acceptance Criteria
- [ ] Completing a collection to 100% (via `collections-core` hook) creates exactly one sticky `UserAchievement`; repeating completion does not duplicate.
- [ ] Removing ratings after unlock does **not** remove achievement or pins.
- [ ] Letterboxd Top 500 achievement remains valid even though collection membership never changes.
- [ ] Each Oscar season collection has its own achievement slug (e.g. `oscars-2026`).
- [ ] Rarity uses denominator = users with ≥1 rated card; API returns `holders_count` and `rarity_percent`.
- [ ] Celery task recalculates rarity; module docstring includes crontab; task registered in `celery_app.py`.
- [ ] User can pin up to 3 unlocked achievements; 4th pin rejected; pins appear on public profile API and UI.
- [ ] `make backend-test` covers unlock, sticky, rarity, pins; `cd frontend && npm run lint && npm run build` clean for touched files.

## Constraints
- **Dependency:** do not implement collection progress itself — consume `collections-core` completion hook and collection slugs only.
- **Docker-first** for migrations, pytest, Celery task tests (`make backend-test`, `.cursor/tech.md`).
- **Service shape:** `@dataclass`, `build()`, single `execute()`, typed errors mapped in routes.
- **Sticky unlock** is a hard product invariant — no code path deletes `UserAchievement` on progress regression.
- **No Celery Beat in-repo** — document schedule only; external crontab invokes worker-accessible task name.
- **Frontend:** `@telegram-apps/telegram-ui`; ESLint clean on touched files.

## References
- **`collections-core`** (prerequisite) — `.cursor/features/collections-core/feature.md`: collection definitions, progress %, 100% completion hook.
- **`docs/features/celery-redis-workers.md`** — worker registration, external scheduling, no Beat.
- **`backend/src/tasks/monthly_recap.py`** — module docstring crontab + `register_tasks` pattern.
- **`profile-gamification-stamps`** — prior gamification patterns (`.cursor/features/profile-gamification-stamps/feature.md`).
- **`profile-and-public-profiles`** — public profile API surface (`.cursor/features/profile-and-public-profiles/feature.md`).
