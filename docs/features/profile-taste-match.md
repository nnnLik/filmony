# Profile Taste Match

## Overview

Users see **taste peers** — profiles in their subscription network with the highest overlap in rated films. Each peer shows a **similarity percentage** (Jaccard on shared `film_id` titles) and a **shared films count**. The list lives in the profile Statistics tab under **Социальность** («Похожие профили»).

Shipped as **v1** alongside [profile analytics redesign](./profile-analytics-redesign.md). A future **v2** may add weighted signals (tags, genres, rating agreement); see `.cursor/features/profile-taste-match/feature.md` for the extended spec.

## Behavior

- **Pool:** followers ∪ following of the profile being viewed.
- **Cards counted:** rated, non-planned cards with a non-null `film_id`.
- **Score:** Jaccard similarity — `shared_films / (profile_films + peer_films - shared_films)`, rounded to three decimals, displayed as 0–100% in UI.
- **Limit:** top 5 peers by shared count (tie-break: `user_id`).
- **Empty state:** «Пока нет похожих профилей» when the profile has no rated films or no network overlap.

## API

`GET /api/users/:id/stats` — additive field on existing response:

```json
{
  "social": {
    "mutual_subscriptions_count": 2,
    "taste_peers": [
      {
        "id": "…",
        "profile_slug": "alice",
        "display_name": "Alice",
        "photo_url": "…",
        "similarity_score": 0.42,
        "shared_films_count": 8
      }
    ]
  }
}
```

## UI

- **Component:** `SocialTastePeers` in `frontend/src/components/profile/ProfileStatsCharts.tsx`
- **Integration:** `ProfileStatsPanel` → Социальность sub-tab
- **Navigation:** tap peer → public profile `/u/:id`

## Backend

- **Service:** `GetUserProfileSocialInsightsService` (`backend/src/services/profile/get_user_profile_social_insights.py`)
- **Schemas:** `TastePeerItemResponse`, `UserProfileSocialInsightsResponse` in `backend/src/api/profile/schemas.py`

## Tests

- `backend/src/tests/api/test_profile_routes.py` — `test_user_stats_social_insights` and related stats coverage

Run (Docker):

```bash
make backend-test-one target=src/tests/api/test_profile_routes.py::test_user_stats_social_insights
```

## Verification status

- **Production:** live (confirmed 2026-07-27)
- **Manual testing:** verified in production by product owner

## Related: taste-quiz knowledge %

Not the same metric as this feature. **[Taste knowledge badge everywhere](./taste-knowledge-badge-everywhere.md)** shows taste-quiz **accuracy %** next to users in feed, comments, and lists — meaning **how well the viewer knows that user's ratings** (viewer → owner), not Jaccard film overlap.

## Limitations (v1)

- Film-backed cards only (`film_id`); games / `catalog_item` overlap not counted.
- No tag, genre, or rating-agreement signals.
- No pairwise compare endpoint or public-profile header badge.
- Peers limited to subscription network, not global discovery.
