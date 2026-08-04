# Profile Taste Match — Decision Log

**Status:** v2 defaults locked for weighted taste match (2026-08-04)

| § | Topic | Decision | Date | Rationale |
|---|-------|----------|------|-----------|
| 1 | Comparison pool | **A** — followers ∪ following only | 2026-07-27 | Same network as v1 |
| 2 | Title identity key | **`catalog_item_id` when present, else `film_id`**; planned excluded | 2026-08-04 | Universal cards + games |
| 3 | Signal catalog + weights | **S1** Jaccard titles (0.35), **S2** tag overlap (0.25), **S4** rating agreement (0.25), **S6** favorites Jaccard (0.15) | 2026-08-04 | Weighted v2 composite |
| 4 | Scoring formula | Linear weighted sum → `score_v2` in `0..1`, 3 decimal places | 2026-08-04 | Deterministic, testable |
| 5 | Tag weighting | Exact tag string Jaccard across all rated cards | 2026-08-04 | v2 baseline |
| 6 | Privacy & breakdown | Aggregate signal coefficients only; no shared title list in API | 2026-08-04 | Avoid sensitive leakage |
| 7 | API shape | Extend `/stats` → `social.taste_peers[]` with additive `score_v2` + `breakdown`; keep v1 `similarity_score` | 2026-08-04 | Backward compatible |
| 8 | UI surfaces | Stats → Социальность → accordion breakdown per peer | 2026-08-04 | Explain the score |
| 9 | Performance | Batch-load network cards + tags; top 5 by `score_v2` | 2026-08-04 | Avoid N+1 |
| 10 | Golden test fixtures | `test_taste_match_v2_golden` + updated social insights test | 2026-08-04 | Regression guard |

## Weight table (§3 + §4) — v2 defaults

| Signal | Weight | Min sample | Included |
|--------|--------|------------|----------|
| S1 Shared rated titles (Jaccard on identity key) | 0.35 | peer ≥3 rated cards | yes |
| S2 Tag overlap (Jaccard) | 0.25 | — | yes |
| S4 Rating agreement `1 − avg_delta/9` on shared titles | 0.25 | ≥3 shared titles | yes (0 if below) |
| S6 Favorites Jaccard | 0.15 | — | yes |

## v1 compatibility

- `similarity_score` remains **film_id-only Jaccard** (v1 formula).
- Ranking and primary UI percentage use **`score_v2`**.

## Sign-off

- [x] v1 shipped (2026-07-27)
- [x] v2 defaults recorded (2026-08-04)
