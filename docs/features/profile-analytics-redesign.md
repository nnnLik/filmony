# Profile Analytics Redesign

## Overview
The profile page header and Statistics tab were redesigned to feel like a social taste narrative instead of a flat dashboard.

## Profile header
- Replaced five large counter tiles with `ProfileCompactMetrics`: a horizontal scrollable strip of compact chips (followers, following, rated, later, favorites).
- Chips navigate to subscriptions or drill into Cards tab segments where applicable.

## Statistics tab
Four internal sub-tabs:

| Tab | Content |
|-----|---------|
| **Обзор** | Activity heatmap, KPI strip, insight cards, taste polarity |
| **Вкус** | Rating bars, tag bubbles, company/mood flow, shelves, years |
| **Социальность** | Mutual subscriptions, watch company, mood, similar profiles |
| **Рейтинги** | Top/worst rated lists |

The activity heatmap is centered in its card so it reads as the main visual anchor instead of a left-aligned grid.

## API (`GET /api/users/:id/stats`)
Additive fields on existing response:

- `tag_taste`: `{ tag, count, average_rating }[]`
- `insights`: `{ activity_total_180d, dominant_company, dominant_mood_after, top_tag }`
- `social`: `{ mutual_subscriptions_count, taste_peers[] }` where peers are ranked by shared rated films (Jaccard similarity).

The heatmap covers a 6-month window end-to-end, with the API range and the UI label kept in sync.

## Tests
- `backend/src/tests/api/test_profile_routes.py` — aggregates and social insights coverage.
