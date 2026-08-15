# Profile Heatmap & Stats Regroup

## Metadata

| Field | Value |
|-------|-------|
| Feature slug | `profile-heatmap-stats-regroup` |
| Status | `in_progress` |
| Stack | frontend |
| Created | 2026-08-15 |

## Problem

Activity heatmap currently lives inside the **Статистика** tab (Overview sub-tab), which buries a high-signal social signal behind an extra navigation step. Stats sub-tabs have grown to five (**Обзор**, **Вкус**, **Социальность**, **Рейтинги**, **Награды**), forcing users to hunt across tabs for related content (top/worst lists vs overview metrics; passport/achievements vs social).

## Goal

Surface the GitHub-style activity heatmap on the profile chrome (own + public profiles) and regroup analytics into **three** stats sub-tabs — **Обзор**, **Вкус**, **Сообщество** — without removing any existing analytics blocks or changing backend APIs.

## Scope

### In scope

**Heatmap on profile chrome**

- New `ProfileActivityHeatmapSection` renders after profile header / bio / pinned achievements and **before** `ProfileMainTabs` on both `ProfilePage` and `PublicProfilePage`.
- Heatmap uses existing `ProfileActivityHeatmap` + `useUserMovieCardStatsQuery` data (`activity_distribution`, shelf filter via `activity_category_id`).
- Heatmap window is the **last 30 days** (last month): `activity_start`/`activity_end`/`activity_distribution` span 30 days; UI copy «за последний месяц».
- Day tap drill: set `completedOn` + `categoryId` (selected shelf) + `sort: 'recent'` on rated-cards query, switch to `movies` / `rated`, scroll to rated panel (reuse `drillToRatedCards` pattern).
- Heatmap must **not** render inside `ProfileStatsPanel` or any stats sub-tab.

**Stats sub-tab regroup (exactly 3 tabs)**

| Tab | Label | Content (all blocks preserved) |
|-----|-------|--------------------------------|
| `overview` | **Обзор** | Metric strip, insights, rating contrast, polarity, top movies, worst movies |
| `taste` | **Вкус** | Rating-scale donut; combined **Теги** (bubble chart + popular tag chips); combined **Как смотрю** (company + mood donuts); shelves, genres, people, franchises, decades |
| `community` | **Сообщество** | Taste-quiz teaser (own profile), mutual subscriptions, similar profiles, passport panel (when `showPassportCollection`), achievements (when `showAchievements`) |

**Removed as separate tabs (content moved, not deleted)**

- **Рейтинги** → top/worst lists + popular tag chips absorbed into **Обзор** / **Вкус** respectively.
- **Награды** → passport + achievements absorbed into **Сообщество**.

**Rename**

- **Социальность** → **Сообщество** (tab id may stay `community` / `social` internally; label must be **Сообщество**).

### Out of scope

- Backend API contract changes (`GET /api/users/:id/stats` response shape unchanged).
- Heatmap cell sizing or streak legend UX changes (see `profile-activity-heatmap`, `profile-streak-stats-legend-ux`).
- New analytics metrics or chart types.
- Profile header metric strip redesign.

## Acceptance criteria

- [ ] `ProfileActivityHeatmapSection` appears on own profile (`ProfilePage`) and public profile (`PublicProfilePage`) after header/bio/pins and before `ProfileMainTabs`.
- [ ] Heatmap does **not** appear inside `ProfileStatsPanel` or the stats tab.
- [ ] Heatmap grid shows the **last 30 days** (last month); header/aria copy references «за последний месяц».
- [ ] Stats insight **За 6 месяцев** (`activity_total_180d`) remains a **180-day** rollup (unchanged).
- [ ] Tapping a heatmap day sets `completedOn`, shelf `categoryId`, `sort: 'recent'`, switches to movies/rated, and scrolls to rated cards.
- [ ] Stats sub-tabs are exactly **Обзор**, **Вкус**, **Сообщество** (no **Рейтинги**, no **Награды**, no **Социальность** label).
- [ ] **Обзор** shows: metric strip, insights, rating contrast, polarity, top movies, worst movies.
- [ ] **Вкус** shows: rating donut; **Теги** section with bubble chart + popular tag chips; **Как смотрю** section with company + mood donuts; shelves, genres, people, franchises, decades.
- [ ] **Сообщество** shows: taste-quiz teaser (own profile when enabled), mutual subscriptions, similar profiles, passport panel (when enabled), achievements (when enabled).
- [ ] Every analytics block that existed before this feature still renders somewhere in stats (no data loss).
- [ ] Backend limits heatmap fields to 30 days (`HEATMAP_WINDOW_DAYS`); existing stats query hooks and drill handlers reused.
- [ ] `queueMicrotask` used for any `setState` inside effects (existing pattern).
- [ ] No `eslint-disable` for `@typescript-eslint/no-unsafe-*` or `react-hooks/*` in touched files.
- [ ] `cd frontend && npm run lint && npm run build` pass.
- [ ] Closeout: `result.md`, `docs/features/profile-heatmap-stats-regroup.md` (later milestone).

## References

| Path | Purpose |
|------|---------|
| `.cursor/features/profile-activity-heatmap/feature.md` | Original heatmap scope (stats-tab placement — superseded for placement only) |
| `.cursor/features/profile-analytics-redesign/feature.md` | Prior analytics sub-tab structure |
| `.cursor/features/profile-stats-people-restructure/feature.md` | Recent **Награды** / taste-social dedupe work |
| `frontend/src/components/profile/ProfileActivityHeatmap.tsx` | Heatmap grid component |
| `frontend/src/components/profile/ProfileStatsPanel.tsx` | Stats sub-tabs and block layout |
| `frontend/src/pages/ProfilePage.tsx` | Own profile page shell |
| `frontend/src/pages/PublicProfilePage.tsx` | Public profile page shell |
