# Plan — profile-rating-contrast-stats

1. Add `compute_rating_contrast_insights` service over rated cards + film external ratings.
2. Wire into `GetUserCardStatsService` → `rating_contrast` on stats API.
3. Frontend types + `ProfileStatsPanel` section and insight cards on Overview.
4. Add KP passport backfill script for prod data gap.
5. Fix API/UI field mismatch (`avg_delta_*`, `biggest_gap`, `compared_count`).
6. Tests and docs closeout.
