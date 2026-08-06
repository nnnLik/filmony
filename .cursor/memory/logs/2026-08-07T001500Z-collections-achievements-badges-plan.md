# Action log fragment

- **Timestamp:** 2026-08-07T001500Z
- **Feature slugs:** `collections-core`, `film-award-badges`, `achievements-rarity-profile-pins`
- **Action type:** plan
- **Summary:** Three decomposed feature specs + plans for Collections, Oscar film badges, achievements rarity/pins

## Files

- `.cursor/features/collections-core/feature.md`
- `.cursor/active/collections-core/plan.md`
- `.cursor/active/collections-core/progress.md`
- `.cursor/features/film-award-badges/feature.md`
- `.cursor/active/film-award-badges/plan.md`
- `.cursor/active/film-award-badges/progress.md`
- `.cursor/features/achievements-rarity-profile-pins/feature.md`
- `.cursor/active/achievements-rarity-profile-pins/plan.md`
- `.cursor/active/achievements-rarity-profile-pins/progress.md`

## Verification

n/a (specs only)

## Key decisions

- Badges independent of collections — Oscar award metadata is a separate curated dataset on `Film`, not driven by collection membership
- Top 500 never updates — Letterboxd Top 500 list is frozen at import; no live sync
- Celery + external crontab — rarity refresh and award sync run as Celery tasks triggered by external crontab, not in-app schedulers
- Sticky achievements — collection-completion unlocks persist even if the user later deletes a rating
- Progress = rated only — collection progress counts films the user has rated, not watchlist or other signals
