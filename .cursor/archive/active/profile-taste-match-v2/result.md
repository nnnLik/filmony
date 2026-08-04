# Result — profile-taste-match-v2

Status: **done**

## Implemented
- Weighted taste match v2 (S1/S2/S4/S6) with `score_v2` + `breakdown` on `/stats`
- v1 `similarity_score` retained for compatibility
- SocialTastePeers accordion breakdown

## Files
- `backend/src/services/profile/compute_weighted_taste_match.py`
- `backend/src/services/profile/get_user_profile_social_insights.py`
- `backend/src/api/profile/schemas.py`
- `frontend/src/components/profile/ProfileStatsCharts.tsx`
- `frontend/src/api/profileTypes.ts`
- `backend/src/tests/api/test_taste_match_v2_golden.py`

## Verification
- `make backend-test-one target=src/tests/api/test_taste_match_v2_golden.py`
- `make backend-test-one target=src/tests/api/test_profile_routes.py::test_user_stats_social_insights`
