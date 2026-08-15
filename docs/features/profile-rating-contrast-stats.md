# Profile rating contrast stats

Compares the user's card ratings with Kinopoisk and IMDb aggregates on **Profile → Statistics → Overview**.

## UI

Section **«Оценки vs КП и IMDb»** (between «Инсайты» and «Полярность оценок»):

| Metric | Meaning |
|--------|---------|
| Средняя дельта КП / IMDb | Mean `user_rating − external_rating` |
| Совпадение с агрегаторами | Share with \|Δ\| ≤ 1 |
| Контр-культ | Count with \|Δ\| ≥ 4 |
| Самый большой разрыв | Film with max \|Δ\| (link to film or card) |

When no external ratings exist on the user's rated films, a hint explains that passport sync is pending.

Selected metrics also appear in the **Инсайты** grid on Overview.

## API

`GET /api/users/:id/stats` → `rating_contrast`:

```json
{
  "avg_delta_kinopoisk": 0.3,
  "avg_delta_imdb": -0.1,
  "biggest_gap": { "film_title": "...", "film_id": 1, "card_id": 42, "gap": 4.5 },
  "agreement_percent": 62.5,
  "contrarian_count": 3,
  "compared_count": 120
}
```

Detailed outlier fields (`kinopoisk_biggest_positive`, etc.) remain for debugging/extension.

## Backend

- `compute_rating_contrast_insights.py` — pure logic over rated cards.
- `get_user_card_stats.py` — loads `rating_kinopoisk` / `rating_imdb` from film rows.

## Ops — backfill KP ratings

```bash
docker compose exec backend python src/manage_backfill_film_kinopoisk_passport.py [--dry-run] [--limit N]
```

Run after deploy when films lack passport ratings needed for contrast stats.

## Verification

```bash
make backend-test-one target=src/tests/unit/services/profile/test_compute_rating_contrast_insights.py
make backend-test-one target=src/tests/integration/api/test_profile_routes.py::test_user_stats_rating_contrast_with_external_ratings
cd frontend && npm run lint && npm run build
```
