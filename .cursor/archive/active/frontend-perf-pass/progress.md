# Progress: frontend-perf-pass

## Status: complete

### Baseline (2026-08-04)
- Build: pass
- index CSS: ~140 KB raw / ~19 KB gzip
- useRatedCardsQueryFromUrl chunk: ~73 KB raw / ~19 KB gzip
- ProfilePage: ~19 KB gzip, FeedPage: ~13 KB gzip

### Completed
- Phase 0: feature.md, plan.md, baseline
- 1.1 Feed batch badges + tests
- 1.2 Lazy ProfileStatsPanel (Profile + PublicProfile)
- 1.3 Tailwind @source, movieCardDetailAnimations.css, removed orphan CreateCardPage.css
- 2.1 profileQueryKeys + hooks
- 2.2–2.3 ProfilePage + PublicProfilePage RQ migration + defer
- 2.4 ProfileStatsPanel RQ, rankings limit 5
- 3 Deeplink fix + tests
- Verification: lint/build/test pass, result.md + docs published

### After metrics
- useRatedCardsQueryFromUrl chunk: ~26 KB / ~8 KB gzip
- ProfileStatsPanel: separate lazy chunk ~47 KB / ~12 KB gzip
- Tests: 90/90
