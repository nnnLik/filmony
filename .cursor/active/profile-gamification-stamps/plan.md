# Plan: profile-gamification-stamps

Полный план: `.cursor/plans/profile_gamification_stamps_f5dfee63.plan.md` (не редактировать).

## Порядок фаз

| Фаза | Содержание | Блокеры |
|------|------------|---------|
| **0** | Артефакты, Film metadata + migration, Kinopoisk staff/sequels, backfill, community avg, `GET /api/me/gamification` | — |
| **1** | Pepe-судья (frontend-only) | нет |
| **2** | Полка-физика (backend service + `ProfileShelfPhysics`) | фаза 0.5 или client fallback |
| **3** | Контр-культ badge | community avg (0.4) |
| **4** | Кино-паспорт UI + `ComputePassportStampsService` | Film.countries backfill |
| **5** | Марафоны director/franchise | staff/sequels metadata |

## Рекомендуемая поставка

1. Pepe-судья — сразу (quick win)
2. Film metadata + community avg — параллельно
3. Contrarian badge → shelf physics → passport → marathons

## Touchpoints (кратко)

**Backend:** `Film` model, Kinopoisk DTOs/transport, `EnrichFilmGamificationMetadataService`, backfill script, `get_catalog_community_stats.py`, `compute_*` gamification services, `api/gamification/routes.py`, pytest.

**Frontend:** `ContrarianBadge`, `ProfilePassportPanel`, `MarathonShelfFrame`, `ProfileShelfPhysics`, `usePepeExtremeRatingJudge`, `gamificationApi.ts`, правки `ProfileStatsPanel` / `ProfilePage` / `MoviePosterGrid` / rated card forms.

## Verification

- `make backend-test` (+ `test_gamification_routes.py`)
- `make backfill-film-gamification-metadata DRY_RUN=1`
- `cd frontend && npm run lint && npm run build`
