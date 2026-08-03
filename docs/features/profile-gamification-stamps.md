# Profile gamification stamps

Five playful profile features that reward film-watching habits: a stamp passport, contrarian badge, director/franchise marathons, shelf physics, and Pepe the judge on extreme ratings.

## Scope (v1)

All gamification logic applies to **film-backed rated cards** only (cards linked to a Kinopoisk `Film`). Games, manual cards, and planned (unrated) cards are excluded.

## Features

### Кино-паспорт (stamp collection)

Collect stamps as you rate films from different countries and eras.

| Stamp | Rule |
|-------|------|
| First country | First rated film from a new country |
| First of decade | First rating for a film from a new decade |
| 5 countries in year | 5+ distinct countries in one calendar year |
| Globe tiers | 5 / 10 / 20 unique countries total |
| First rating of year | Meta-stamp: first rated card in a calendar year |

**Where:** own profile → Stats → sub-tab **«Коллекция»** (`ProfilePassportPanel`). Locked stamps show progress; unlocked stamps show the film that earned them.

**Public profile:** visitors see unlocked stamps only via `GET /api/users/{id}/gamification/passport`.

### Бейдж «контр-культ»

A medal on **your own** rated cards when your score diverges from the community average by ≥ 4.0 points and at least 3 other users have rated the same film.

**Where:** profile grid, card detail, your own feed cards (`ContrarianBadge`).

### Режиссёрский / франшизный марафон

Achievement when you have rated **5+ films** by the same primary director or within the same franchise (from Kinopoisk staff / sequels metadata).

**Where:** passport panel + shelf frame on own profile. Tap a marathon chip to filter rated cards by title search.

### Полка-физика (shelf physics)

Visual mood on your **rated** shelf:

| State | Trigger |
|-------|---------|
| `slump` | 3+ consecutive ratings ≤ 3 |
| `glow` | 3+ consecutive ratings ≥ 9 |
| `neutral` | otherwise |

Respects `prefers-reduced-motion` (static tint, no animation).

### Pepe-судья

Frontend-only easter egg: when you pick **1** or **10** while creating or editing a rated card, Pepe delivers a random phrase. Fires once per threshold crossing (debounced), not on every drag tick.

## API

| Endpoint | Auth | Returns |
|----------|------|---------|
| `GET /api/me/gamification` | required | passport, marathons, shelf_physics |
| `GET /api/users/{id}/gamification/passport` | public | unlocked stamps only |

Card list/detail responses include `community_avg_rating` and `is_contrarian` where applicable.

## Data & backfill

Film metadata columns: `countries`, `primary_director_kinopoisk_id`, `primary_director_name`, `franchise_key`.

## Director filters (v1.1)

- `GET /api/users/{id}/cards?director_kinopoisk_id=` — rated cards by primary director.
- `GET /api/users/{id}/cards?franchise_key=` — rated cards in the same Kinopoisk franchise cluster.
- `GET /api/users/{id}/rated-directors` — dropdown source: `{ kinopoisk_id, name, count }[]`.
- Profile UI: director filter in rated-cards panel; marathon chip drill-down sets director/franchise filter (not title search).

## Passport stamps (v1.1 additions)

| Stamp | Rule |
|-------|------|
| `director_first_{kp_id}` | First rated film per director |
| `director_fan_{kp_id}` | 3 films by same director (progress 3/3) |
| `genres_total_{5,10,15}` | Distinct genres milestone |
| `first_rating_10` / `first_rating_1` | First 10 or 1 rating |
| `binge_day` | 3+ ratings same calendar day |
| `chrono_year_{2020..2030}` | 3 film decades in one calendar year |
| `horror_survivor` | 5+ horror/ужасы films |
| `high_streak_3` | 3 consecutive ratings ≥ 9 |
| `mood_swings` | Within 7 days: rating ≤3 and ≥9 |

Collection UI groups stamps by category: country, decade, director, genre, vibe, extreme, milestone.

Populated lazily on Kinopoisk resolve and via backfill:

```bash
make backfill-film-gamification-metadata DRY_RUN=1
make backfill-film-gamification-metadata
```

Run backfill after deploy so existing films qualify for passport stamps and marathons.

## Key files

| Layer | Path |
|-------|------|
| Stamp catalog | `backend/src/const/passport_stamps.py`, `frontend/src/lib/gamification/passportStamps.ts` |
| Gamification services | `backend/src/services/gamification/` |
| API routes | `backend/src/api/gamification/routes.py` |
| Frontend hook | `frontend/src/hooks/useGamification.ts` |
| Passport UI | `frontend/src/components/profile/gamification/ProfilePassportPanel.tsx` |
| Shelf physics | `frontend/src/components/profile/gamification/ProfileShelfPhysics.tsx` |
| Pepe judge | `frontend/src/hooks/usePepeExtremeRatingJudge.ts` |

## Limitations

- Film-backed cards only; no passport/marathon for games or manual entries.
- Existing films need backfill before retroactive stamps/marathons appear.
- Marathon drill-down uses title search, not a dedicated filter API.
- «Первая ч/б» stamp deferred to v2 (no reliable B&W metadata).

## Verification

```bash
make backend-test-one target=src/tests/api/test_gamification_routes.py
make backend-test-one target=src/tests/providers/test_kinopoisk_gamification_dtos.py src/tests/services/gamification/test_enrich_film_gamification_metadata.py
cd frontend && npm run lint && npm run build
```
