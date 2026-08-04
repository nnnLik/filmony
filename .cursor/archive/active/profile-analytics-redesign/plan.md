# Profile Analytics Redesign — Plan

1. Backend: extend `GetUserCardStatsService` with `tag_taste`, `insights`; add `GetUserProfileSocialInsightsService`; wire into `GET /users/:id/stats`.
2. Frontend: `ProfileCompactMetrics` for profile header; rebuild `ProfileStatsPanel` with 4 sub-tabs and new chart components.
3. Align TypeScript types with API response shapes.
4. Refine the stats heatmap so the grid is centered in its available card width and the window spans 6 months.
5. Verify: `make backend-test-one target=src/tests/api/test_profile_routes.py`, `npm run lint && npm run build`.
