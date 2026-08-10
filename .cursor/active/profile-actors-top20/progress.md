# Progress — profile-actors-top20

**Status:** completed  
**Started:** 2026-08-10  
**Closed:** 2026-08-10T134500Z

## Log

| When | Action |
|------|--------|
| 2026-08-10T133700Z | Kickoff: created `feature.md`, `plan.md`, `progress.md`; registered in HOT as `in_progress` #1. |
| 2026-08-10T134000Z | Backend: capped `actor_distribution` at 20 via SQL `LIMIT`; removed `unique_actors_count` from insights DTO and API schema. |
| 2026-08-10T134100Z | Backend tests: regression asserts for absent `unique_actors_count`; new integration test for 20-actor cap and preserved `top_actor_*`. |
| 2026-08-10T134200Z | Frontend: removed `unique_actors_count` type and «Актёров» metric strip; replaced actor donut with collapsible `ActorDistributionList` (10 default, expand to 20). |
| 2026-08-10T134500Z | Verification: 38 profile API integration tests passed; `npm run lint && npm run build` clean. Closeout docs and HOT update. |
