---
name: profile-filters-persistence
overview: Persist profile filter selections in the URL so they survive opening a card and returning to the profile, including reloads and shared links.
todos:
  - id: serialize-query
    content: Add URL serialization helpers and tests for rated card filters.
    status: completed
  - id: sync-profile-pages
    content: Hydrate profile filter state from search params and keep it synced on both profile pages.
    status: completed
  - id: preserve-return-navigation
    content: Verify card detail return flow keeps the filtered profile URL intact.
    status: completed
  - id: verify-and-document
    content: Run frontend lint/build, then update delivery docs and action logs.
    status: completed
isProject: false
---

# Profile Filters Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep profile filter selections stable when the user opens a card from the profile and returns back, without losing the current filter state.

**Architecture:** Move the profile rating filter query from page-local React state into URL search params on both profile screens. The filter UI stays controlled, but the page becomes responsible for hydrating the query from the URL on mount and writing changes back to the URL on every filter update. Card detail navigation can remain a plain route transition because the profile state will now be recoverable from the URL.

**Tech Stack:** React, React Router, TypeScript, existing `RatedCardsListQuery` helpers, frontend tests.

---

### Task 1: Add URL serialization helpers for profile filters

**Files:**
- Modify: `frontend/src/lib/ratedCardsListQuery.ts`
- Test: `frontend/src/lib/ratedCardsListQuery.test.ts` or the nearest existing test file for this helper

- [ ] **Step 1: Write the failing test**

```ts
import { describe, it, expect } from 'vitest';
import { DEFAULT_RATED_CARDS_QUERY, ratedCardsToListParams } from './ratedCardsListQuery';

describe('ratedCardsListQuery url helpers', () => {
  it('serializes and restores a non-default filter query', () => {
    const query = {
      ...DEFAULT_RATED_CARDS_QUERY,
      search: 'thriller',
      sort: 'top',
    };

    const params = ratedCardsToListParams(query);
    expect(params).toMatchObject({ search: 'thriller', sort: 'top' });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- ratedCardsListQuery.test.ts -w 1`
Expected: the test fails until URL parsing/serialization support exists.

- [ ] **Step 3: Write minimal implementation**

Add a small pair of helpers that convert between `RatedCardsListQuery` and `URLSearchParams`:

```ts
export function ratedCardsQueryToSearchParams(query: RatedCardsListQuery): URLSearchParams {
  const params = new URLSearchParams();
  // only persist non-default values so URLs stay compact
  return params;
}

export function ratedCardsQueryFromSearchParams(searchParams: URLSearchParams): RatedCardsListQuery {
  return {
    ...DEFAULT_RATED_CARDS_QUERY,
  };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- ratedCardsListQuery.test.ts -w 1`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/ratedCardsListQuery.ts frontend/src/lib/ratedCardsListQuery.test.ts
git commit -m "feat: persist profile filters in url"
```

### Task 2: Hydrate and sync profile filter state in page components

**Files:**
- Modify: `frontend/src/pages/ProfilePage.tsx`
- Modify: `frontend/src/pages/PublicProfilePage.tsx`
- Modify: `frontend/src/components/profile/ProfileRatedCardsFilters.tsx` only if the current controlled API needs a small prop shape adjustment
- Test: nearest page/component tests for profile screens, if present

- [ ] **Step 1: Write the failing test**

Add/extend a test that renders the profile page with search params, changes a filter, and verifies the URL updates without resetting the selected values after remount.

```ts
it('restores profile filters from the URL after remount', async () => {
  // render profile at /profile?search=thriller&sort=top
  // assert filter controls show the URL-backed values
  // trigger a card open/return flow or remount the page
  // assert the same filter values remain selected
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- ProfilePage.test.tsx -w 1`
Expected: fail because the page still initializes from `DEFAULT_RATED_CARDS_QUERY` only.

- [ ] **Step 3: Write minimal implementation**

In both pages:
- read initial state from `location.search`
- keep `ratedQuery` in component state for the controlled UI
- push updates back into the URL with `navigate({ search: ... }, { replace: true })` or the equivalent router API
- preserve unrelated query params if the page already uses them

```ts
const [ratedQuery, setRatedQuery] = useState(() =>
  ratedCardsQueryFromSearchParams(new URLSearchParams(location.search))
);

useEffect(() => {
  navigate({ search: ratedCardsQueryToSearchParams(ratedQuery).toString() }, { replace: true });
}, [ratedQuery, navigate]);
```

Keep the implementation small and avoid introducing a new store unless the router approach cannot cover both profile variants.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- ProfilePage.test.tsx -w 1`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/ProfilePage.tsx frontend/src/pages/PublicProfilePage.tsx frontend/src/components/profile/ProfileRatedCardsFilters.tsx
git commit -m "feat: keep profile filters in the url"
```

### Task 3: Verify card navigation keeps the profile URL intact

**Files:**
- Modify: `frontend/src/pages/MovieCardDetailPage.tsx` only if the current back navigation drops search params
- Test: nearest navigation test, if present

- [ ] **Step 1: Write the failing test**

Add a regression test for opening a card from a filtered profile and returning to the same filtered URL.

```ts
it('returns to the same profile url with filters intact', async () => {
  // start at /profile?search=thriller
  // open a card
  // navigate back
  // assert the profile route still includes ?search=thriller
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- MovieCardDetailPage.test.tsx -w 1`
Expected: fail if back navigation currently strips search params or if the test harness catches remount loss.

- [ ] **Step 3: Write minimal implementation**

If needed, make back navigation preserve the current location when there is a known profile referrer; otherwise rely on URL-backed profile state and leave the existing `navigate(-1)` behavior alone.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- MovieCardDetailPage.test.tsx -w 1`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/MovieCardDetailPage.tsx frontend/src/pages/ProfilePage.tsx frontend/src/pages/PublicProfilePage.tsx
git commit -m "fix: preserve profile filters after card return"
```

### Task 4: Run frontend verification and update docs artifacts

**Files:**
- Modify: `.cursor/active/<feature-slug>/progress.md`
- Modify: `.cursor/active/<feature-slug>/result.md`
- Modify: `docs/features/<feature-slug>.md`
- Modify: `.cursor/memory/logs/<relevant-fragment>.md`

- [ ] **Step 1: Run the required checks**

Run: `cd frontend && npm run lint && npm run build`
Expected: both pass with no new warnings or errors in touched files.

- [ ] **Step 2: Confirm behavior manually if needed**

Open a profile, apply filters, open a card, go back, and verify the same filters are still selected and reflected in the URL.

- [ ] **Step 3: Write the delivery artifacts**

Document what changed, which files were touched, how it was verified, and any edge cases left intentionally out of scope.

- [ ] **Step 4: Commit docs/memory updates**

```bash
git add .cursor/active/<feature-slug>/progress.md .cursor/active/<feature-slug>/result.md docs/features/<feature-slug>.md .cursor/memory/logs/<relevant-fragment>.md
git commit -m "docs: record profile filter persistence"
```
