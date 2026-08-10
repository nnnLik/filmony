# Action log fragment

- **Timestamp:** 2026-08-10T134500Z
- **Feature slug:** profile-actors-top20
- **Action type:** closeout
- **Summary:** Capped profile `actor_distribution` at top 20; removed `unique_actors_count` from API/insights; replaced Taste actor donut with collapsible ranked list (10 default, expand to 20); kept «Любимый актёр» insight.
- **Files:**
  - `backend/src/services/profile/get_user_card_stats.py`
  - `backend/src/api/profile/schemas.py`
  - `backend/src/tests/integration/api/test_profile_routes.py`
  - `frontend/src/api/profileTypes.ts`
  - `frontend/src/components/profile/ProfileStatsPanel.tsx`
  - `docs/features/profile-actors-top20.md`
  - `.cursor/active/profile-actors-top20/result.md`
- **Verification:**
  - `make backend-test-one target=src/tests/integration/api/test_profile_routes.py` — 38 passed
  - `cd frontend && npm run lint && npm run build` — clean
