# Profile Analytics Redesign — Result

**Status:** done

## Implemented
- Compact profile metrics strip (`ProfileCompactMetrics`) on own and public profiles.
- Stats tab with four sub-sections; heatmap-first Overview.
- New chart widgets: TagBubbleChart, TasteFlowStrip, ProfileInsightsGrid, SocialTastePeers.
- Extended `GET /api/users/:id/stats` with:
  - `tag_taste[]` — tag count + average rating
  - `insights` — activity_total_180d, dominant_company, dominant_mood_after, top_tag
  - `social` — mutual_subscriptions_count, taste_peers (Jaccard similarity on shared films)
- Follow-up heatmap tweak: centered grid layout and a 6-month activity window.

## Changed files
- `backend/src/services/profile/get_user_profile_social_insights.py`
- `backend/src/services/profile/get_user_card_stats.py`
- `backend/src/api/profile/schemas.py`
- `backend/src/api/profile/users_routes.py`
- `backend/src/tests/api/test_profile_routes.py`
- `frontend/src/components/profile/ProfileCompactMetrics.tsx`
- `frontend/src/components/profile/ProfileActivityHeatmap.tsx`
- `frontend/src/components/profile/ProfileStatsPanel.tsx`
- `frontend/src/components/profile/ProfileStatsCharts.tsx`
- `frontend/src/pages/ProfilePage.tsx`
- `frontend/src/pages/PublicProfilePage.tsx`
- `frontend/src/api/profileTypes.ts`

## Verification
- `make backend-test-one target=src/tests/api/test_profile_routes.py` — 36 passed
- `make backend-test-one target=src/tests/api/test_profile_routes.py::test_user_stats_social_insights` — passed
- `cd frontend && npm run lint && npm run build` — passed

## Known limitations
- Taste peers computed only for film-backed cards in followers/following network.
- Social similarity is film_id overlap (Jaccard), not tag/genre weighted yet.
- The broader profile analytics redesign remains a larger workstream; this update only tightens the heatmap presentation and range.
