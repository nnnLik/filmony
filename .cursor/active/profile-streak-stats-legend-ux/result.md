# profile-streak-stats-legend-ux — result

Status: **complete**

## Implemented
- Streak badge tap/hover explainer with RU pluralization (`formatDaysCount`)
- Donut legend collapse (top-8 + «Ещё N» / «Свернуть») for genre/director/franchise/decade charts
- Removed marathon shelf from rated cards tab (`ProfileRatedPanel`)
- Removed «Посты» tab from own and public profile pages

## Changed files
- `frontend/src/lib/formatRuPlural.ts`
- `frontend/src/components/streaks/RatingStreakBadge.tsx`
- `frontend/src/components/profile/ProfileStatsCharts.tsx`
- `frontend/src/components/profile/ProfileStatsPanel.tsx`
- `frontend/src/pages/MonthlyRecapPage.tsx`
- `frontend/src/components/profile/ProfileRatedPanel.tsx`
- `frontend/src/components/profile/ProfileMainTabs.tsx`
- `frontend/src/pages/ProfilePage.tsx`
- `frontend/src/pages/PublicProfilePage.tsx`

## Verification
```bash
cd frontend && npm run lint && npm run build
```
Both pass.

## Known limitations
- Backend still returns full distribution arrays; collapse is frontend-only
- `ProfilePostsPanel.tsx` retained but not mounted on profile pages; feed posts remain on `FeedPage`

## Next steps
- Manual QA on device: streak tooltip in feed cards, stats legend expand/collapse
