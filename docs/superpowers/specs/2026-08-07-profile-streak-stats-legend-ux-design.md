# Profile streak explainer + donut legend collapse + remove rated marathon shelf + remove Posts tab — Design Spec

**Date:** 2026-08-07  
**Status:** approved  
**Feature slug:** `profile-streak-stats-legend-ux`

---

## 1. Context

Profile surfaces show a rating streak badge (visible when streak > 3), taste distribution donut charts with long legends (genre, director, franchise), and a marathon shelf above the rated films grid. Users need clearer streak meaning without avatar animations; long donut legends clutter stats tabs; the rated tab marathon shelf duplicates passport/gamification content elsewhere. The profile «Посты» tab duplicates feed-post browsing already available on the global feed; removing it simplifies the profile to Карточки + Статистика.

---

## 2. Goals

1. **Streak explainer** — Explain the rating streak number via tap (mobile) and hover (desktop) on the badge everywhere it appears. No avatar cloud animation.
2. **Donut legend collapse** — Collapse director/genre/franchise (and other long) donut legends to top-8 rows plus «Ещё N» expand control.
3. **Remove rated marathon shelf** — Remove `MarathonShelfFrame` from `ProfileRatedPanel` / rated cards tab only. Keep passport/gamification elsewhere.
4. **Remove Posts tab** — Hide the «Посты» main tab and its panel on **both** own profile (`ProfilePage`) and public profile (`PublicProfilePage`). Feed posts remain on the global feed and via API; only the profile-tab surface is removed.

---

## 3. Non-goals

- No backend distribution limit and no new streak API fields.
- No avatar-origin bubble animation.
- Do not delete `MarathonShelfFrame.tsx` or gamification API (still used by `ProfilePassportPanel`, shelf physics).
- Do not remove feed posts globally: keep `FeedPage` posts segment, feed-post creation, `useUserFeedPostsInfiniteQuery`, backend `ListUserFeedPostsService`, and `ProfilePostsPanel.tsx` (file retained; profile pages stop importing/mounting it).

---

## 4. Remove Posts tab

### 4.1 Surfaces (both have Posts tab today)

| Page | Route | Tab control | Posts panel |
|------|-------|-------------|-------------|
| Own profile | `/profile` → `ProfilePage` | `ProfileMainTabs` | `ProfilePostsPanel` (no `Section` wrapper) |
| Public profile | `/u/:userId` → `PublicProfilePage` | `ProfileMainTabs` | `Section header="Посты"` wrapping `ProfilePostsPanel` |

Shared tab definition: `frontend/src/components/profile/ProfileMainTabs.tsx` — three segments (`Карточки`, `Посты`, `Статистика`), `grid-cols-3`, type `ProfileMainTab = 'movies' | 'posts' | 'stats'`.

**Not in scope:** `FeedPage` has its own «Посты» feed segment (`segmentLabel: 'Посты'`) — leave unchanged.

### 4.2 ProfileMainTabs

- Remove `{ value: 'posts', label: 'Посты' }` from `segments`.
- Change `ProfileMainTab` to `'movies' | 'stats'` only.
- Update `gridColsClassName` from `grid-cols-3` to `grid-cols-2`.

### 4.3 ProfilePage (`frontend/src/pages/ProfilePage.tsx`)

Remove all posts-tab wiring:

- Import of `ProfilePostsPanel`.
- `postsQuery` (`useUserFeedPostsInfiniteQuery`, enabled when `mainTab === 'posts'`).
- `feedPosts` memo, `postsErr`, `postsLoading`, `postsLoadMoreRef`, `onProfilePostDeleted` handler (if only used for posts panel).
- Conditional render block `{mainTab === 'posts' ? <ProfilePostsPanel … /> : null}`.

Keep `ProfileMainTabs`, movies segment, and stats tab unchanged.

### 4.4 PublicProfilePage (`frontend/src/pages/PublicProfilePage.tsx`)

Same removals as §4.3, plus:

- Remove `Section header="Посты"` wrapper around `ProfilePostsPanel`.
- Remove `onPublicProfilePostDeleted` handler if only used for posts panel.

### 4.5 Unchanged (feed posts live elsewhere)

- `frontend/src/components/profile/ProfilePostsPanel.tsx` — file retained (no profile mount after this change).
- `frontend/src/pages/FeedPage.tsx` — global feed «Посты» segment.
- `useUserFeedPostsInfiniteQuery` hook and backend `list_user_feed_posts` API.
- `frontend/src/hooks/useProfileMoviesContent.ts` — already gates on `mainTab === 'movies'` only; no posts references to remove.

### 4.6 Routing / deep-links

Profile main tab is **local React state** (`useState<ProfileMainTab>('movies')`) on both pages — **not** synced to URL query params.

Existing profile URL params are unrelated to main tab:

- `?movies=watchlist` / `?movies=rated` — movies sub-segment (`useProfileMoviesSegmentFromUrl`).
- Rated-cards filter keys (`filmTitle`, `sort`, etc.) — `useRatedCardsQueryFromUrl`.

There is **no** `/profile?tab=posts`, `/profile?mainTab=posts`, or equivalent deep-link today. **No redirect or fallback handler is required** for removed tab state.

---

## 5. Streak badge explainer

### 5.1 Files

- **Primary:** `frontend/src/components/streaks/RatingStreakBadge.tsx`
- **Pass-through:** `frontend/src/components/streaks/RatingStreakAuthorBadge.tsx` — delegates to `RatingStreakBadge`; no duplicate tooltip logic

### 5.2 Interaction pattern

Mirror `frontend/src/components/tasteQuiz/TasteQuizKnowledgeBadge.tsx`, plus desktop hover:

- Wrap badge in a **button** with toggle open/close on tap.
- `role="tooltip"` on the popover panel (same pattern as `TasteQuizKnowledgeBadge`).
- `stopPropagation` on badge click so parent cards/links do not activate.
- **Desktop hover (addition):** `onMouseEnter` / `onMouseLeave` on the wrapper to open/close the tooltip in addition to tap toggle.

### 5.3 Visibility

Unchanged: badge renders only when current streak **> 3**.

### 5.4 Copy (RU)

| Element | Text |
|---------|------|
| `aria-label` | «Серия оценок: {N} {день\|дня\|дней} подряд» |
| Tooltip title | «Серия оценок» |
| Tooltip body | «{N} {день\|дня\|дней} подряд вы ставите оценки фильмам.» |

Use `frontend/src/lib/formatRuPlural.ts`: add `formatDaysCount(count)` via the existing private `ruPluralForm` pattern (`день` / `дня` / `дней`), then use it in `aria-label` and tooltip body.

### 5.5 Call sites

No call-site changes — badge continues to be used via `AuthorBadge` / `RatingStreakAuthorBadge` as today.

---

## 6. Donut legend collapse

### 6.1 File

`ProfileStatsCharts.tsx` — `StatsDonutChart` component.

### 6.2 Prop

```tsx
legendCollapsedTopN?: number
```

Pass `legendCollapsedTopN={8}` only where segment lists can exceed eight rows:

| Caller | `StatsDonutChart` sections | Pass `8`? |
|--------|---------------------------|-----------|
| `ProfileStatsPanel` | По жанрам, По режиссёрам, По сериям, По десятилетиям | Yes |
| `ProfileStatsPanel` | Оценки по шкале, Компания, После просмотра, По полкам | No (bounded small sets) |
| `MonthlyRecapPage` | Жанры, Десятилетия | Yes |

Omit the prop elsewhere (default = show full legend).

### 6.3 Donut ring vs legend

- **Donut ring** always uses **full** `visibleSegments` (count > 0) — collapse affects **legend list only**, not the chart segments.

### 6.4 Collapsed legend order

**Decision:** preserve existing segment order from API — take the **first 8** of `visibleSegments`. Do **not** re-sort in the frontend; API already returns count-desc for genre/director/franchise distributions.

### 6.5 Expand / collapse controls

- Collapsed state: show ≤ `legendCollapsedTopN` legend rows; if more remain, show button **«Ещё {remaining}»** (`remaining = total - topN`).
- Expanded state: show full list; show **«Свернуть»** to collapse again.

### 6.6 Active segment outside top-N

When `activeValue` is set and not among the top-N legend rows, **auto-expand** the legend so the active row is visible. Do not pin a row into the collapsed set — prefer full expand for clarity.

### 6.7 Segment click

Unchanged for all visible legend rows (collapsed or expanded).

---

## 7. Remove rated marathon shelf

### 7.1 ProfileRatedPanel

- Unwrap / remove `MarathonShelfFrame` from rated tab content.
- Remove `unlockedMarathons` and `onMarathonDrill` props from component API; drop `hasGamification` gate that required all three marathon props.
- When `shelfPhysicsMode` is set, wrap the rated grid in `ProfileShelfPhysics` directly (no marathon frame).

### 7.2 ProfilePage

- Stop passing marathon-related props to `ProfileRatedPanel`.
- Keep `gamificationQuery` for `shelfPhysicsMode` and stats drill flows that remain on other tabs.

### 7.3 Unchanged

- `ProfilePassportPanel` — marathon shelf and gamification display remain.
- `MarathonShelfFrame.tsx` — file retained; used by passport and shelf physics paths.

---

## 8. Acceptance criteria

- [ ] Streak badge shows explainer on tap and on hover (desktop).
- [ ] Genre/director/franchise/decade legends (profile stats + monthly recap) show ≤8 rows until expand.
- [ ] Rated tab no longer shows marathon list above grid.
- [ ] Own profile (`/profile`) and public profile (`/u/:userId`) show only **Карточки** and **Статистика** tabs — no «Посты» tab or posts panel.
- [ ] Global feed posts segment on `FeedPage` still works.
- [ ] Passport/marathon elsewhere still works.
- [ ] Frontend lint/build clean for touched files.

---

## 9. Verification

```bash
cd frontend && npm run lint && npm run build
```

**Manual:**

- Profile → stats → taste tabs (genre, director, franchise): legend collapse/expand, active segment auto-expand.
- Feed and profile: streak badge tooltip on tap and desktop hover; aria-label correct for plural forms.
- Own profile and public profile: two tabs only (Карточки, Статистика); no posts list on profile.
- Feed page: «Посты» segment still loads posts.

---

## 10. Files touched (implementation reference)

| Area | Files |
|------|-------|
| Streak | `frontend/src/components/streaks/RatingStreakBadge.tsx`, `RatingStreakAuthorBadge.tsx`, `frontend/src/lib/formatRuPlural.ts` |
| Donut legend | `frontend/src/components/profile/ProfileStatsCharts.tsx`, `ProfileStatsPanel.tsx`, `frontend/src/pages/MonthlyRecapPage.tsx` |
| Rated shelf | `ProfileRatedPanel.tsx`, `ProfilePage.tsx` |
| Remove Posts tab | `ProfileMainTabs.tsx`, `ProfilePage.tsx`, `PublicProfilePage.tsx` |

**Not deleted:** `MarathonShelfFrame.tsx`, gamification API modules, `ProfilePassportPanel` marathon integration, `ProfilePostsPanel.tsx`, feed-post API/hooks, `FeedPage` posts segment.
