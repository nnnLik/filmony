# profile-taste-match v2 — result

Status: **done**

## Implemented
- `ComputeWeightedTasteMatchService` — Jaccard 0.35, tags 0.25, rating agreement 0.25, favorites 0.15.
- `GetUserProfileSocialInsightsService` delegates to weighted service; min 3 peer cards.
- API: `TasteMatchBreakdownResponse`, `score_v2` on `TastePeerItemResponse`.
- Frontend: `SocialTastePeers` accordion breakdown; types in `profileTypes.ts`.
- `decisions.md` v2 section updated.

## Verification
- `make backend-test-one target=src/tests/api/test_profile_taste_match_v2.py` — passed
- `make backend-test-one target=src/tests/api/test_profile_routes.py::test_user_stats_social_insights` — v1 regression
