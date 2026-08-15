# Profile heatmap & stats regroup — integration findings

**Date:** 2026-08-15  
**Scope:** Cross-cutting consistency pass across heatmap extraction, stats sub-tab regroup, profile page wiring, HOT registry.

---

## Verdict: issues found (2 material, 1 minor)

Integration is largely aligned with design. Heatmap is out of stats; tab ids/labels match **Обзор / Вкус / Сообщество**; analytics blocks are preserved in the expected tabs. Two drill/prop gaps on `PublicProfilePage` and one dead prop on `ProfileStatsPanel`.

---

## Issues

### 1. `PublicProfilePage` — community tab & marathon drill parity gap

**Files:** `frontend/src/pages/PublicProfilePage.tsx`, `frontend/src/pages/ProfilePage.tsx`

`ProfilePage` passes full community/rewards wiring to `ProfileStatsTab`:

- `showTasteQuizTeaser`
- `showAchievements`
- `onMarathonDrill={handleMarathonDrill}`

`PublicProfilePage` passes only `showPassportCollection` and `onDrillToRatedCards` — no taste-quiz teaser, achievements, or marathon drill handler (even when `isOwnPublicProfile` is true).

**Impact:**

- Own profile via `/u/:id` → **Сообщество** missing «Угадай вкус» teaser and `AchievementsPanel` that `/profile` shows.
- Any public profile (own or other) → passport marathon shelf clicks have no `onMarathonDrill` handler (drill wiring broken for `ProfilePassportPanel` → `MarathonShelfFrame`).

**Fix:** Mirror `ProfilePage` props when appropriate:

- `showTasteQuizTeaser={isOwnPublicProfile}`
- `showAchievements={isOwnPublicProfile}`
- `onMarathonDrill={handleMarathonDrill}` (define handler like `ProfilePage`, or share a small hook)

---

### 2. `ProfileStatsPanel` — `enableCategoryFilter` dead prop

**Files:** `frontend/src/components/profile/ProfileStatsPanel.tsx`, `frontend/src/components/profile/ProfileStatsTab.tsx`

`enableCategoryFilter` is declared on `ProfileStatsPanelProps` (comment: shelf filter for rated-cards tab) and passed from `ProfileStatsTab`, but `ProfileStatsPanel` does not destructure or use it.

**Impact:** No functional bug today (category filter lives on rated-cards panel via page props), but misleading API surface and unused prop threading from both profile pages.

**Fix:** Remove prop from `ProfileStatsPanel` / `ProfileStatsTab` and page call sites, **or** wire it if stats panel still needs it (unlikely after regroup).

---

### 3. (Minor) `ProfileActivityHeatmapSection` — silent error vs stats panel

**File:** `frontend/src/components/profile/ProfileActivityHeatmapSection.tsx`

On stats load failure, heatmap section returns `null` (no user-visible error). `ProfileStatsPanel` shows a destructive error message for the same query when `activityCategoryId` is `null`.

**Impact:** Heatmap can vanish silently while stats tab still shows an error (or vice versa if only heatmap query fails with shelf filter). Low severity; UX inconsistency only.

---

## HOT.md registry

**File:** `.cursor/HOT.md`

| Check | Result |
|-------|--------|
| `profile-heatmap-stats-regroup` in `in_progress` | ✅ #1 |
| `film-radarr-playback` preserved | ✅ #2 |
| `collections-core` preserved | ✅ #3 |
| `film-award-badges` preserved | ✅ #4 |
| `achievements-rarity-profile-pins` preserved | ✅ #5 |
| Required slugs dropped | ❌ none dropped |
| Extra slug added | ⚠️ `feed-created-sort` listed as #6 `in_progress` (matches git worktree; not one of the four slugs named in the integration checklist, but legitimate concurrent work) |

---

## Verified clean

| Check | Result | Evidence |
|-------|--------|----------|
| `ProfileActivityHeatmap` import removed from stats panel | ✅ | `ProfileStatsPanel.tsx` has no `ProfileActivityHeatmap` import; only `ProfileActivityHeatmapSection.tsx` imports it |
| Stats query uses `null` activity category | ✅ | `useUserMovieCardStatsQuery(userId, null, …)` in `ProfileStatsPanel` (~line 582) |
| Heatmap section owns shelf-filtered stats query | ✅ | `ProfileActivityHeatmapSection` uses `activityCategoryId` from shelf selection |
| Stats sub-tabs exactly 3 | ✅ | `StatsSubTab = 'overview' \| 'taste' \| 'community'`; labels **Обзор / Вкус / Сообщество** |
| Old tab ids/labels removed | ✅ | No `Социальность`, `Рейтинги`, `Награды`, `activity`, `social`, `ratings`, `rewards` in profile stats components |
| **Обзор** content | ✅ | Metric strip, insights, contrast, polarity, top, worst |
| **Вкус** content | ✅ | Rating donut, tags (bubble + popular chips), company, mood, shelves, genres, people, franchises, decades |
| **Сообщество** content (when flags set) | ✅ | Taste-quiz teaser, mutual, peers, passport, achievements |
| Popular tags in taste, not overview | ✅ | `prioritizedPopularTags` block under `statsSubTab === 'taste'` |
| Top/worst in overview | ✅ | Under `statsSubTab === 'overview'` |
| Heatmap before main tabs (own profile) | ✅ | `ProfilePage.tsx` — `ProfileActivityHeatmapSection` then `ProfileMainTabs` |
| Heatmap before main tabs (public profile) | ✅ | `PublicProfilePage.tsx` — same order after pins |
| `handleHeatmapDaySelect` on both pages | ✅ | Sets `completedOn`, `categoryId`, `sort: 'recent'` + `drillToRatedCards()` |
| Broken imports in touched files | ✅ | All imports resolve to existing modules |
| Stats drill to rated cards | ✅ | `onDrillToRatedCards` passed from both pages; tag/genre/franchise/shelf/decade handlers call it |
| React Query cache sharing (heatmap + stats, no shelf) | ✅ | Both use `activityCategoryId === null` → same `userMovieCardStatsQueryKey` |

---

## Analytics block inventory (no data loss)

| Block | Tab | Present |
|-------|-----|---------|
| Metric strip | Обзор | ✅ |
| Insights | Обзор | ✅ |
| Rating contrast | Обзор | ✅ |
| Polarity | Обзор | ✅ |
| Top movies | Обзор | ✅ |
| Worst movies | Обзор | ✅ |
| Rating donut | Вкус | ✅ |
| Tag bubbles | Вкус | ✅ |
| Popular tag chips | Вкус | ✅ |
| Company donut | Вкус | ✅ |
| Mood donut | Вкус | ✅ |
| Shelves donut | Вкус | ✅ |
| Genres donut | Вкус | ✅ |
| People | Вкус | ✅ |
| Franchises donut | Вкус | ✅ |
| Decades donut | Вкус | ✅ |
| Taste-quiz teaser | Сообщество | ✅ (own `/profile` only; see issue #1) |
| Mutual subscriptions | Сообщество | ✅ |
| Taste peers | Сообщество | ✅ |
| Passport panel | Сообщество | ✅ (when `showPassportCollection`) |
| Achievements | Сообщество | ✅ (own `/profile` only; see issue #1) |
| Activity heatmap | Profile chrome | ✅ (not in stats) |
