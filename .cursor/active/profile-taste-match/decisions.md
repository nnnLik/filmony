# Profile Taste Match — Decision Log

**Status:** resolved — shipped to production (2026-07-27)

Pre-implementation §1–§10 checklist was deferred during build; closeout records the **as-shipped v1** behavior confirmed in production. A future v2 may revisit open items in `.cursor/features/profile-taste-match/feature.md`.

| § | Topic | Decision | Date | Rationale |
|---|-------|----------|------|-----------|
| 1 | Comparison pool | **A** — followers ∪ following only | 2026-07-27 | Matches shipped `GetUserProfileSocialInsightsService` network query |
| 2 | Title identity key | **`film_id` only** | 2026-07-27 | v1 Jaccard on rated, non-planned film-backed cards |
| 3 | Signal catalog + weights | **S1 only** (shared rated titles / Jaccard) | 2026-07-27 | v1 baseline; weighted signals deferred to v2 |
| 4 | Scoring formula | **Jaccard:** `shared / union`, output `0..1` | 2026-07-27 | Implemented in `_load_taste_peers` |
| 5 | Tag/genre weighting | **Not included in v1** | 2026-07-27 | Deferred |
| 6 | Privacy & breakdown | Peers from public network; shared count + score only | 2026-07-27 | No non-public title leakage beyond existing profile rules |
| 7 | API shape | **Option A** — extend `/stats` → `social.taste_peers[]` | 2026-07-27 | Additive fields on existing stats response |
| 8 | UI surfaces | Stats → **Социальность** → «Похожие профили» | 2026-07-27 | `SocialTastePeers` component |
| 9 | Performance & caching | On-demand per `/stats` request; top 5 peers | 2026-07-27 | `TASTE_PEERS_LIMIT = 5` |
| 10 | Golden test fixtures | Covered in `test_user_stats_social_insights` | 2026-07-27 | API-level regression tests in profile routes suite |

## Weight table (§3 + §4) — v1 as shipped

| Signal | Weight | Min sample | Included |
|--------|--------|------------|----------|
| Shared rated titles (Jaccard) | 1.0 | ≥1 rated film on profile | yes |

## Sign-off

- [x] Shipped and verified in production (user confirmation, 2026-07-27)
- [ ] v2 weighted formula / UI breakdown — future work if product reopens spec
