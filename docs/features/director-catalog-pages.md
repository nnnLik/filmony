# Director catalog pages

## Overview

Shows primary director on movie cards with a color-coded chip linking to a director filmography page. Only films with at least one Filmony rating appear on the director page.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/directors/{kinopoisk_id}` | Summary: name, films_count, avg_community_rating |
| GET | `/api/directors/{kinopoisk_id}/films?cursor&limit` | Paginated rated films with genres + community stats |

Card/film payloads include `film_primary_director_*` (cards/feed) or `primary_director_*` (`FilmResponse`).

## Frontend

- `DirectorChip` — deterministic color per Kinopoisk director id → `/directors/:kinopoiskId`
- Surfaces: card detail, feed card, film detail
- `DirectorDetailPage` — film list → `/films/:filmId` (community ratings)

## Ops

Director metadata requires `primary_director_*` on `Film` (backfill: `manage_backfill_film_gamification_metadata.py`).

## Tests

- `backend/src/tests/api/test_directors_routes.py`
- `frontend/src/lib/__tests__/directorColor.test.ts`
