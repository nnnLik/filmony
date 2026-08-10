# Profile Stats People Restructure

## Metadata

| Field | Value |
|-------|-------|
| Feature slug | `profile-stats-people-restructure` |
| Status | `in_progress` |
| Stack | fullstack |
| Created | 2026-08-10 |

## Problem

Profile stats sub-tabs and people sections feel fragmented and visually flat:

- **Коллекция** and **Достижения** are separate tabs even though both are “rewards / gamification” content; users hunt across tabs for passport stamps and achievement pins.
- **Вкус** and **Социальность** both surface company («С кем смотрите») and mood («Эмоции после») data — Taste uses donut charts, Social repeats the same distributions as summary rows.
- **По режиссёрам** and **По актёрам** use vertical ranked lists with small avatars; actors already receive `poster_url` from the API, but directors do not — and the list layout underuses portrait photos compared to the rest of the app.

## Goal

Simplify stats navigation, deduplicate social vs taste content, and present directors/actors as horizontal scrollable portrait cards with visible photos.

## Scope

### In scope

**Sub-tab restructure**

- When achievements are shown (`showAchievements`), merge **Коллекция** + **Достижения** into a single sub-tab **«Награды»** that hosts passport collection (`ProfilePassportPanel`) and achievements (`AchievementsPanel`) in one scrollable view (clear section headers).
- When achievements are hidden (e.g. other user’s profile without achievements), keep **Коллекция** only if `showPassportCollection`; do not show an empty **Награды** tab.
- Deduplicate company/mood between **Вкус** and **Социальность**: **Вкус** keeps interactive donut charts for company and mood; **Социальность** removes duplicate company/mood blocks and keeps social-only content (mutual subscriptions, taste-quiz teaser, similar profiles / taste peers).

**People sections (directors & actors)**

- Replace vertical `DirectorDistributionList` / `ActorDistributionList` with **horizontal scrollable portrait cards** (photo, name, film count, link to person page).
- **Backend:** add `poster_url: str | None` to `DirectorDistributionItem` / API response, sourced from `Film.primary_director_poster_url` when aggregating director counts (pick a representative poster per director — e.g. from highest-rated or most recent rated film; document choice in service).
- **Frontend:** extend `DirectorDistributionItem` type; render `poster_url` on director cards (fallback to initials avatar when missing). Actors already expose `poster_url` — reuse in new horizontal layout.

**Tests & types**

- Backend pytest for `director_distribution[].poster_url` population and null when no poster on source films.
- Update `profileTypes.ts`, profile API schema mapping, and integration tests as needed.

### Out of scope

- Changes to director/actor detail pages beyond consuming existing routes.
- New gamification rules, achievement definitions, or passport stamp logic.
- Redesign of overview, rankings, genre/franchise/decade donuts.
- `docs/features/…` closeout and HOT `recent_completed` (follow-up milestone).

## Acceptance criteria

- [ ] When `showAchievements` is true, stats sub-tabs show **«Награды»** instead of separate **«Коллекция»** and **«Достижения»**; both passport and achievements panels render inside it with distinct section titles.
- [ ] When `showAchievements` is false, tab set matches previous behavior for collection-only profiles (no orphan **Достижения** tab).
- [ ] **Вкус** tab still shows company and mood donut charts with existing drill/filter behavior.
- [ ] **Социальность** tab no longer shows duplicate «С кем смотрите» / «Эмоции после» blocks; mutual subscriptions, taste-quiz teaser (when enabled), and «Похожие профили» remain.
- [ ] **По режиссёрам** and **По актёрам** use horizontal scroll rows of portrait cards with visible photos (not vertical lists).
- [ ] `GET` profile stats returns `director_distribution[].poster_url` (nullable) aligned with backend aggregation rules.
- [ ] `actor_distribution` horizontal UI uses existing `poster_url`; director cards use new field with avatar fallback.
- [ ] Backend tests cover `poster_url` on director distribution (present and absent cases).
- [ ] Frontend `npm run lint && npm run build` pass on touched files.
- [ ] Closeout: `result.md`, `docs/features/profile-stats-people-restructure.md` (later).

## References

| Path | Purpose |
|------|---------|
| `frontend/src/components/profile/ProfileStatsPanel.tsx` | Sub-tabs, taste/social sections, director/actor lists |
| `frontend/src/api/profileTypes.ts` | Client types for stats payload |
| `backend/src/services/profile/get_user_card_stats.py` | Director/actor distribution assembly |
| `backend/src/api/profile/schemas.py` | API response models |
| `backend/src/models/film.py` | `primary_director_poster_url` source field |
| `.cursor/features/profile-directors-top20/feature.md` | Prior director distribution work |
| `.cursor/features/profile-actors-top20/feature.md` | Prior actor distribution work |
