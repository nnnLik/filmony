# Profile streak explainer, stats legend collapse, profile simplification

## Summary
Frontend UX improvements for profile and stats surfaces:

1. **Rating streak badge** — tap or hover shows «Серия оценок: N дней подряд» tooltip (visible when streak > 3).
2. **Donut legends** — genre, director, franchise, and decade charts show top-8 rows with «Ещё N» expand.
3. **Rated tab** — marathon shelf removed from cards grid (passport/gamification elsewhere unchanged).
4. **Profile tabs** — «Посты» tab removed; only Карточки and Статистика remain. Global feed posts unchanged.

## Key files
- `frontend/src/components/streaks/RatingStreakBadge.tsx`
- `frontend/src/components/profile/ProfileStatsCharts.tsx` (`StatsDonutChart.legendCollapsedTopN`)
- `frontend/src/components/profile/ProfileMainTabs.tsx`
- `frontend/src/pages/ProfilePage.tsx`, `PublicProfilePage.tsx`

## Design spec
`docs/superpowers/specs/2026-08-07-profile-streak-stats-legend-ux-design.md`

## Verification
```bash
cd frontend && npm run lint && npm run build
```
