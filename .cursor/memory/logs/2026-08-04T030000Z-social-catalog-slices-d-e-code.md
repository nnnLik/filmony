# Action log — 2026-08-04 profile-taste-match-v2 + monthly-recap

- **Timestamp:** 2026-08-04T030000Z
- **Feature slug:** profile-taste-match-v2, monthly-recap
- **Action type:** code
- **Summary:** Implemented taste match v2 (weighted score + breakdown) and monthly recap (API, UI, Telegram nudge).
- **Files:**
  - `backend/src/services/profile/compute_weighted_taste_match.py`
  - `backend/src/services/profile/build_monthly_recap.py`
  - `backend/src/tasks/monthly_recap.py`
  - `frontend/src/pages/MonthlyRecapPage.tsx`
  - `frontend/src/components/profile/ProfileStatsCharts.tsx`
- **Verification:** `make backend-test-one target=src/tests/api/test_taste_match_v2_golden.py`; `make backend-test-one target=src/tests/api/test_monthly_recap_routes.py`; `cd frontend && npm run lint && npm run build`
