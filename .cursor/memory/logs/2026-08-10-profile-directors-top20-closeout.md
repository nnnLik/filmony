# Action log fragment

- **Timestamp:** 2026-08-10T180000Z
- **Feature slug:** profile-directors-top20
- **Action type:** closeout
- **Summary:** Capped profile `director_distribution` at top 20; removed `unique_directors_count` from API/insights; replaced Taste director donut with collapsible ranked list (10 default, expand to 20); clickable favorite actor/director insight links with `userId` query; director list and footer links aligned with actor section.
- **Files:**
  - `backend/src/services/profile/get_user_card_stats.py`
  - `backend/src/api/profile/schemas.py`
  - `backend/src/tests/integration/api/test_profile_routes.py`
  - `frontend/src/api/profileTypes.ts`
  - `frontend/src/components/profile/ProfileStatsPanel.tsx`
  - `frontend/src/components/profile/ProfileStatsCharts.tsx`
  - `docs/features/profile-directors-top20.md`
  - `docs/features/profile-stats-director-franchise.md`
  - `.cursor/active/profile-directors-top20/result.md`
- **Verification:**
  - `make backend-test-one target=src/tests/integration/api/test_profile_routes.py`
  - `cd frontend && npm run lint && npm run build`
