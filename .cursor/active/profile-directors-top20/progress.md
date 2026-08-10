# Progress — profile-directors-top20

**Status:** complete  
**Started:** 2026-08-10  
**Closed:** 2026-08-10T180000Z

## Log

| When | Action |
|------|--------|
| 2026-08-10T170000Z | Kickoff: created `feature.md`, `plan.md`, `progress.md`; registered in HOT as `in_progress` #1. |
| 2026-08-10T175000Z | Backend: director distribution capped at 20; `unique_directors_count` removed; `top_director_*` from sorted list `[0]`. |
| 2026-08-10T175500Z | Frontend: `DirectorDistributionList`, removed director donut; clickable actor/director insights. |
| 2026-08-10T176000Z | Integration tests: `test_user_stats_director_distribution_capped_at_twenty`, negative asserts for removed fields. |
| 2026-08-10T180000Z | Closeout: fixed director `userId` links (list, insight, footer); docs, result, action-log, HOT moved to `recent_completed` #1. |
