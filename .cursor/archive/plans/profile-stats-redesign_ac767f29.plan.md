---
name: profile-stats-redesign
overview: Rework the Profile > Statistics area into a clearer, tabbed analytics experience that prioritizes readability, compact charts, and practical filters/sorts while reusing the existing profile stats data.
todos:
  - id: stats-structure
    content: Define the 3-tab stats hierarchy and map each existing metric into overview, taste, or rankings.
    status: completed
  - id: stats-layout
    content: Redesign the stats cards and charts for a one-column, no-horizontal-scroll mobile layout.
    status: completed
  - id: stats-filters
    content: Integrate compact filters and sort controls into the stats flow and align them with rated-cards filtering.
    status: completed
  - id: stats-drilldown
    content: Wire chart/chip/rank interactions so users can drill from stats into filtered cards or card details.
    status: completed
  - id: stats-verify
    content: Validate empty states, public vs owner views, and responsive behavior across the redesigned stats surface.
    status: completed
isProject: false
---

# Profile Statistics Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the profile statistics tab into a tabbed analytics view that is easy to scan, stays readable on mobile without sideways scrolling, and surfaces the most useful stats first.

**Architecture:** Keep the existing stats data source, but reorganize the UI into a small set of sub-tabs so each view has a single job: overview, taste breakdowns, and ranked lists/drill-downs. Use one-column mobile-first layouts, stacked cards, and compact chart components so every graph fits the viewport width naturally.

**Tech Stack:** React, `@telegram-apps/telegram-ui`, existing profile stats API and rated-cards filters.

---

### Task 1: Define the tab structure and content hierarchy

**Files:**
- Modify: `[frontend/src/pages/ProfilePage.tsx](frontend/src/pages/ProfilePage.tsx)`
- Modify: `[frontend/src/components/profile/ProfileStatsPanel.tsx](frontend/src/components/profile/ProfileStatsPanel.tsx)`

**Goal:** Split the current single stats dashboard into 3 sub-tabs with a clear hierarchy.

**Proposed structure:**
- `Обзор`: headline KPIs, a short “what this profile looks like” summary, and the most important high-signal chart.
- `Вкусы`: rating distribution, taste polarity, tags, company, mood-after.
- `Рейтинги`: top rated, lowest rated, year-based trends, and drill-down lists.

**Notes:**
- Keep the main profile tab bar as-is, but make statistics a nested tab set.
- Reuse the current stats data; do not add new backend work unless implementation reveals a missing aggregate.
- Make the first tab the default landing view for the stats section.

### Task 2: Redesign charts and cards for mobile-first readability

**Files:**
- Modify: `[frontend/src/components/profile/ProfileStatsPanel.tsx](frontend/src/components/profile/ProfileStatsPanel.tsx)`
- Create: `[frontend/src/components/profile/ProfileStatsCharts.tsx](frontend/src/components/profile/ProfileStatsCharts.tsx)`
- Create: `[frontend/src/components/profile/ProfileStatsSummaryCard.tsx](frontend/src/components/profile/ProfileStatsSummaryCard.tsx)`

**Goal:** Ensure all charts fit the viewport width and read clearly without horizontal scrolling.

**Layout rules:**
- Use a single vertical column on mobile.
- Place charts in full-width cards with consistent padding and heading hierarchy.
- Prefer compact bars/donuts with fewer labels, smaller tick density, and controlled height.
- Avoid side-by-side chart placement unless there is enough width for it to remain legible.

**Content rules:**
- Keep the two KPI cards, but make them more compact and visually aligned.
- Convert less critical sections into smaller summary cards or compact chip groups.
- Improve the section wording so labels read naturally in Russian.

### Task 3: Add filters and sorting controls to the new stats flow

**Files:**
- Modify: `[frontend/src/components/profile/ProfileRatedCardsFilters.tsx](frontend/src/components/profile/ProfileRatedCardsFilters.tsx)`
- Modify: `[frontend/src/components/profile/ProfileStatsPanel.tsx](frontend/src/components/profile/ProfileStatsPanel.tsx)`

**Goal:** Make filtering feel like a first-class part of analyzing the profile, not a separate hidden tool.

**Initial controls:**
- Period: `все время / год / месяц / custom`
- Sort: `по оценке / по дате / по популярности`
- Content scope: `фильмы / сериалы / все`
- Optional chips: tags, company, mood, favorites-only

**Behavior:**
- Keep the controls compact and sticky only if needed.
- Make each filter choice update both the visible stat summaries and the ranked lists consistently.
- Only show controls that are valid for the current profile context to avoid owner/public mismatches.

### Task 4: Add drill-down interactions from stats into the rated-cards list

**Files:**
- Modify: `[frontend/src/components/profile/ProfileStatsPanel.tsx](frontend/src/components/profile/ProfileStatsPanel.tsx)`
- Modify: `[frontend/src/pages/ProfilePage.tsx](frontend/src/pages/ProfilePage.tsx)`

**Goal:** Let users tap a chart segment, tag chip, or ranked row and jump into the underlying card set with matching filters applied.

**Behavior:**
- Clicking a tag chip filters the rated-cards list by that tag.
- Clicking a rank row opens the corresponding card detail.
- Clicking a company or mood chip narrows the analysis to that slice.
- Preserve the existing back/navigation behavior so the profile remains easy to recover.

### Task 5: Verify visual polish, data coverage, and responsive behavior

**Files:**
- Test/verify: `[frontend/src/components/profile/ProfileStatsPanel.tsx](frontend/src/components/profile/ProfileStatsPanel.tsx)`
- Test/verify: `[frontend/src/pages/ProfilePage.tsx](frontend/src/pages/ProfilePage.tsx)`

**Goal:** Confirm the redesign is readable, consistent, and does not introduce layout regressions.

**Checks:**
- No horizontal scrolling on standard mobile widths.
- Tabs switch cleanly without losing context.
- Existing stats data still renders correctly for empty and populated profiles.
- Public profile mode does not expose owner-only controls.

**Suggested acceptance criteria:**
- The stats area opens on a concise overview, not a dense wall of charts.
- All graphs/cards fit the screen width on mobile.
- At least one clear path exists from each major stat to a filtered list or detail view.
- The UI feels like an analytics surface, not a raw dashboard dump.
