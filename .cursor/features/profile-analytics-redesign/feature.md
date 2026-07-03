# Profile Analytics Redesign

## Metadata
- Feature slug: `profile-analytics-redesign`
- Status: done
- Created at: 2026-07-03

## Goal
Replace bulky profile counter tiles and flat stats dashboard with a compact social header and heatmap-first analytics with taste/social/rankings sub-tabs.

## Acceptance criteria
- [x] Profile header uses compact horizontal metrics strip instead of 5 large tiles.
- [x] Stats tab has sub-tabs: Обзор, Вкус, Социальность, Рейтинги.
- [x] Heatmap remains primary visual in Overview.
- [x] GET `/api/users/:id/stats` extended with `tag_taste`, `insights`, `social` (additive).
- [x] Backend pytest coverage for new stats fields and social insights.
- [x] Frontend lint + build pass.
