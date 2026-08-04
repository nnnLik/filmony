# Profile Taste Match v2

Extends profile stats taste peers with a weighted composite score and per-signal breakdown.

## API

`GET /api/users/{id}/stats` → `social.taste_peers[]`:

- `similarity_score` — v1 film_id Jaccard (unchanged)
- `score_v2` — weighted composite 0..1
- `breakdown` — `{ shared_titles, tag_overlap, rating_agreement, shared_favorites }`

Peers need ≥3 rated cards. Ranking uses `score_v2`.

## Weights

| Signal | Weight |
|--------|--------|
| Title Jaccard (catalog_item_id or film_id) | 0.35 |
| Tag overlap | 0.25 |
| Rating agreement (≥3 shared titles) | 0.25 |
| Favorites Jaccard | 0.15 |

## UI

`SocialTastePeers` in profile stats shows v2 percentage and expandable breakdown.

## Service

`ComputeWeightedTasteMatchService` — `backend/src/services/profile/compute_weighted_taste_match.py`
