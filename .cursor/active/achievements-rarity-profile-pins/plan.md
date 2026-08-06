# Plan: achievements-rarity-profile-pins

**Feature slug:** `achievements-rarity-profile-pins`  
**Status:** `in_progress`  
**Blocked by:** `collections-core` (collection progress + 100% completion hook must ship first)

---

## Dependency order

| Phase | Deliverable | Blocker |
|-------|-------------|---------|
| **0** | `collections-core` merged: collection catalog, user progress, completion hook | — |
| **1** | DB models + migrations + achievement catalog seed | phase 0 |
| **2** | Unlock service wired to completion hook | phase 1 |
| **3** | Rarity service + Celery periodic task | phase 1 |
| **4** | API (me + public profile) | phases 2–3 |
| **5** | Frontend pins + achievements UI | phase 4 |
| **6** | Tests + docs closeout | phases 1–5 |

---

## 1. Data models + migrations

**Files:** `backend/src/models/achievement.py` (or split modules), Alembic migration under `backend/src/migrations/versions/`

### 1.1 `Achievement` (catalog)
- `id` (PK)
- `slug` (unique, stable — e.g. `letterboxd-top-500`, `oscars-2026`)
- `collection_slug` (unique FK or string ref to `collections-core` collection)
- `title`, `description`, `icon_key` (nullable)
- Rarity snapshot fields (updated by periodic task):
  - `holders_count` (int, default 0)
  - `eligible_users_count` (int, default 0)
  - `rarity_percent` (numeric/float, nullable until first calc)
  - `rarity_calculated_at` (timestamptz, nullable)

### 1.2 `UserAchievement` (sticky unlock)
- `id` (PK)
- `user_id` (FK → users)
- `achievement_id` (FK → achievements)
- `unlocked_at` (timestamptz)
- Unique constraint `(user_id, achievement_id)`
- **No** `ON DELETE CASCADE` from progress tables — row persists for life of account

### 1.3 `UserAchievementPin` (profile showcase)
- `id` (PK)
- `user_id` (FK)
- `achievement_id` (FK → achievements; must exist in `UserAchievement` for same user)
- `slot_index` (smallint 0..2) — enforce max 3 in service layer + optional DB check
- Unique `(user_id, slot_index)` and `(user_id, achievement_id)`

### 1.4 Catalog seed
- Migration or data migration script seeds achievements for:
  - Letterboxd Top 500 (`letterboxd-top-500` ↔ static collection slug from `collections-core`)
  - Oscar seasons: one row per season slug (`oscars-2026`, …) as collections are added
- Document: Top 500 membership frozen → achievement definition never changes

---

## 2. Unlock on collection completion (sticky)

**Hook integration (from `collections-core`):**
- When progress hits 100%, call `GrantCollectionAchievementService.build(session).execute(user_id=..., collection_slug=...)`

**File:** `backend/src/services/achievements/grant_collection_achievement.py`

- Resolve `Achievement` by `collection_slug`; if missing → log + no-op (or typed error for ops)
- Insert `UserAchievement` if not exists (`ON CONFLICT DO NOTHING` or select-then-insert)
- **Never** delete on progress drop — no revoke service in v1

**Idempotency:** safe to call on every progress recompute at ≥100%

---

## 3. Rarity recalculation

### 3.1 `RecalculateAchievementRarityService`
**File:** `backend/src/services/achievements/recalculate_achievement_rarity.py`

- `execute(self, achievement_id: int | None = None) -> None` — `None` = all achievements
- **Eligible users:** `COUNT(DISTINCT user_id)` from `UserCard` where rated (not planned-only) — match product rule in feature.md
- **Holders:** `COUNT(DISTINCT user_id)` from `UserAchievement` for achievement
- `rarity_percent = (holders / eligible * 100)` if eligible > 0 else `NULL`
- Update `Achievement` snapshot fields + `rarity_calculated_at`
- Pure aggregation in service; DAO helpers optional

### 3.2 Celery task
**File:** `backend/src/tasks/achievement_rarity.py`

Module docstring (mirror `monthly_recap.py`):

```text
Beat schedule (document only — configure externally):
    recalculate_achievement_rarity: daily 03:00 UTC (crontab minute=0 hour=3)
```

- `register_tasks(app: Celery)` → `@app.task(name='tasks.achievement_rarity.recalculate_achievement_rarity')`
- Use `_run_async_isolated` + async session pattern from `tasks/monthly_recap.py` / `telegram_engagement.py`
- Register in `backend/src/celery_app.py` `_register_all_tasks`

**Ops:** external host crontab triggers task name; see `docs/features/celery-redis-workers.md` (no Beat in-repo)

---

## 4. Profile pins services

### 4.1 `SetUserAchievementPinsService`
**File:** `backend/src/services/achievements/set_user_achievement_pins.py`

- `execute(user_id, achievement_slugs: list[str])` — ordered list, max **3** entries
- Validate each slug unlocked for user
- Replace pin rows transactionally (delete + insert or upsert by slot)
- Errors: `TooManyPins`, `AchievementNotUnlocked`, `AchievementNotFound`

### 4.2 `ListUserAchievementsService`
**File:** `backend/src/services/achievements/list_user_achievements.py`

- Returns catalog merged with user state: locked/unlocked, `unlocked_at`, rarity fields, `is_pinned`, pin order

---

## 5. API routes

**Package:** `backend/src/api/achievements/` (or extend `api/profile/`)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `GET` | `/api/me/achievements` | user | Full list + rarity + pin state |
| `PUT` | `/api/me/achievement-pins` | user | Body: `{ "achievement_slugs": ["...", "..."] }` max 3 |
| `GET` | `/api/users/{identifier}/achievement-pins` | user | Public pinned achievements (or embed in existing public profile response) |

**Public profile extension (preferred):**
- Add `pinned_achievements: [...]` to `PublicProfileResponse` in `backend/src/api/profile/schemas.py` to avoid extra round-trip

**Response DTO fields (each achievement):**
- `slug`, `title`, `description`, `icon_key`
- `unlocked`, `unlocked_at` (null if locked — omit on public pins endpoint)
- `holders_count`, `rarity_percent`, `rarity_calculated_at`
- `collection_slug` (optional, for deep link to collection UI)

Map service errors → 400/404/403 per repo conventions.

---

## 6. Frontend

### 6.1 API client
**File:** `frontend/src/api/achievementsApi.ts`
- `fetchMyAchievements()`, `updateAchievementPins(slugs: string[])`

### 6.2 Own profile — achievements + pin manager
**Files:** e.g. `frontend/src/components/profile/AchievementsPanel.tsx`, `AchievementPinPicker.tsx`
- List achievements with rarity badge (e.g. “2.4% · 18 users”)
- Pin UI: up to 3 slots, drag or tap to assign/unassign
- Locked achievements visible with progress hint from `collections-core` if exposed

### 6.3 Public profile — pinned strip
**Files:** extend `PublicProfilePage` / profile header area
- Show ordered pinned achievements with rarity
- Read-only; link to collection page when available

**UI stack:** `@telegram-apps/telegram-ui`; match profile gamification visual language where sensible.

---

## 7. Tests

### 7.1 Unit (`backend/src/tests/unit/services/achievements/`)
- Rarity math: eligible denominator (≥1 rated card), zero eligible edge case
- Pin validation: max 3, not unlocked, duplicate slugs

### 7.2 Integration (`backend/src/tests/integration/`)
- `test_achievement_unlock.py` — hook grants achievement at 100%; second call idempotent
- `test_achievement_sticky.py` — delete rating / regress progress → `UserAchievement` still exists
- `test_achievement_rarity_task.py` — task updates snapshot counts (may mock time)
- `test_achievement_pins_routes.py` — PUT pins, public GET, 400 on 4th pin
- Register task in `test_celery_app.py` if new module added

**Run:** `make backend-test-one target=src/tests/integration/...` then `make backend-test`

### 7.3 Frontend
- Component tests optional; **required:** `cd frontend && npm run lint && npm run build`

---

## 8. Verification checklist

- [ ] Migration applies cleanly in Docker
- [ ] Completion hook from `collections-core` grants achievement once
- [ ] Sticky unlock survives rating deletion (integration test)
- [ ] Rarity task updates `holders_count` / `rarity_percent`; docstring crontab present
- [ ] Pin limit 3 enforced API + UI
- [ ] Public profile shows pins to other users
- [ ] `make backend-test`; frontend lint + build pass
- [ ] Closeout: `result.md`, `docs/features/achievements-rarity-profile-pins.md`, action-log fragment

---

## Touchpoints summary

**Backend:** models, migration, seed, `grant_collection_achievement`, `recalculate_achievement_rarity`, `set_user_achievement_pins`, `list_user_achievements`, `tasks/achievement_rarity.py`, `celery_app.py`, profile/achievement routes, pytest.

**Frontend:** `achievementsApi.ts`, achievements panel, pin picker, public profile pinned section.

**External:** `collections-core` completion hook; host crontab for `tasks.achievement_rarity.recalculate_achievement_rarity`.
