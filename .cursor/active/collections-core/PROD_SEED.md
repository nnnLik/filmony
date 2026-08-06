# Production seed runbook — collections

Curated manifests (git-tracked):

- `backend/src/data/curated/letterboxd_top_500_kinopoisk.json` (~500 films)
- `backend/src/data/curated/oscars/oscars_{2020..2026}_kinopoisk.json` (67 films total)

Seed scripts are idempotent — safe to re-run.

## Prerequisites

- Backend container running with production `DATABASE_URL`
- Kinopoisk API credentials configured (same as local compose env)
- Collection domain migration applied (`p1q2r3s4t567_collection_domain`)

## 1. Migrate

```bash
docker compose exec -w /opt/app filmony-backend alembic upgrade head
```

Applies collection domain, film award badges, and achievements migrations.

## 2. Dry-run (recommended)

```bash
DRY_RUN=1 make seed-collections
DRY_RUN=1 make seed-achievements
DRY_RUN=1 make sync-film-award-badges
```

## 3. Apply seed (one-shot)

```bash
make seed-collections
make seed-achievements
make sync-film-award-badges
```

Or run individually:

```bash
make seed-letterboxd-top-500
make seed-oscars
```

Single Oscar ceremony year:

```bash
YEAR=2024 make seed-oscars
```

Optional tuning (env vars, passed through Makefile):

```bash
DRY_RUN=1 LIMIT=10 SLEEP=0.5 make seed-collections
```

## Expected counts after full seed

| Collection | Slug | Films |
|------------|------|------:|
| Letterboxd Top 500 | `letterboxd-top-500` | ~500 |
| Oscars 2020 | `oscars-2020` | 9 |
| Oscars 2021 | `oscars-2021` | 8 |
| Oscars 2022 | `oscars-2022` | 10 |
| Oscars 2023 | `oscars-2023` | 10 |
| Oscars 2024 | `oscars-2024` | 10 |
| Oscars 2025 | `oscars-2025` | 10 |
| Oscars 2026 | `oscars-2026` | 10 |
| **Oscars subtotal** | | **67** |

Verify in DB (optional):

```sql
SELECT slug, film_count FROM collection ORDER BY slug;
```

## Notes

- Oscar cup badges live in `film_award_badge` (sync from curated Oscar JSON via `make sync-film-award-badges`).
- Achievement catalog seeded via `make seed-achievements` (1:1 with collection slugs).
- Seed does not touch user progress, pins, or unlocked achievements.
- Re-running updates collection metadata and film links only.

## Crontab (host, external)

Register on prod server (docstrings in task modules):

- `tasks.achievement_rarity.recalculate_achievement_rarity` — daily 03:00 UTC
- `tasks.film_award_badges.sync_film_award_badges` — after Oscar ceremony (e.g. Mar 5 06:00 UTC)
