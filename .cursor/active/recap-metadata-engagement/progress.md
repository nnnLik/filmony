# Progress — recap-metadata-engagement

## 2026-08-04
- Extended `BuildMonthlyRecapService` with director/country/decade/genre breakdown + new countries
- API schemas + frontend MonthlyRecapPage with StatsDonutChart
- Telegram: director in follower new-card DM and subscribed activity digest
- Tests: monthly recap routes, digest message rendering

## 2026-08-04 (v2)
- Monthly recap: `director_breakdown` + `franchise_breakdown` API fields; donut charts on MonthlyRecapPage
- Telegram: country in follower new-card DM and subscribed digest; shared `film_metadata_hint` helper
- Monthly recap nudge: preview lines (films count, top director/country) via `BuildMonthlyRecapService`
- Reactions, card comments/mentions/replies, weekly controversy digest: director/country hints when known
- Tests: recap franchise/director breakdown, digest country, nudge preview, film metadata hint, controversy metadata

## 2026-08-04 (v3)
- Removed marathon pill badges in MonthlyRecapPage + MarathonShelfFrame (plain list rows)
- Franchise labels: `resolve_franchise_label` + marathon achievements use TMDB name → min-KP title → first film title → fallback
- Tests: franchise_label first-film fallback, gamification marathon label assertion
