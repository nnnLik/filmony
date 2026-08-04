# Feature: profile-taste-match-v2

## Metadata
- Feature slug: `profile-taste-match-v2`
- Status: in_progress
- Extends: `profile-taste-match` (v1 Jaccard)

## Goal
Weighted taste match v2 on profile stats with signal breakdown in UI.

## Acceptance
- `/stats` → `social.taste_peers[]` includes `score_v2` + `breakdown`
- v1 `similarity_score` preserved (film_id Jaccard)
- Peers with `< 3` rated cards excluded
- `SocialTastePeers` shows v2 % + expandable breakdown
- Golden pytest fixtures
