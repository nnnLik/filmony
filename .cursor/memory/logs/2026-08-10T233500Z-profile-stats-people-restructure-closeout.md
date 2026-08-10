# Closeout: profile-stats-people-restructure

- **Timestamp:** 2026-08-10T233500Z
- **Feature slug:** profile-stats-people-restructure
- **Action type:** closeout
- **Summary:** Profile stats UX — merged «Коллекция»+«Достижения» into «Награды»; deduped Taste/Social company/mood blocks; horizontal director/actor portrait cards; backend `director_distribution[].poster_url`.

## Files
- `backend/src/services/profile/get_user_card_stats.py`
- `backend/src/api/profile/schemas.py`
- `backend/src/tests/integration/api/test_profile_routes.py`
- `frontend/src/api/profileTypes.ts`
- `frontend/src/components/profile/ProfileStatsPanel.tsx`
- `docs/features/profile-stats-people-restructure.md`
- `.cursor/active/profile-stats-people-restructure/result.md`

## Verification
- `make backend-test-one target=src/tests/integration/api/test_profile_routes.py` — director distribution `poster_url` tests passed
- `cd frontend && npm run lint` — pass
