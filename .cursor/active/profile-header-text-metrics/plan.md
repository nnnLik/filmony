# Plan: profile-header-text-metrics

## Steps

1. Scaffold feature artifacts and HOT entry
2. Rewrite `ProfileCompactMetrics` — two-line text strip, keep props/callbacks
3. Extend `ProfileHeader` — left avatar row, optional embedded metrics, taste-quiz badge toggle
4. Wire `ProfilePage` and `PublicProfilePage` to shared header; left-align bio/CTA
5. Lint + build; closeout docs

## Files

- `frontend/src/components/profile/ProfileCompactMetrics.tsx`
- `frontend/src/components/profile/ProfileHeader.tsx`
- `frontend/src/pages/ProfilePage.tsx`
- `frontend/src/pages/PublicProfilePage.tsx`
