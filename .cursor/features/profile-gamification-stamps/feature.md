# Profile Gamification Stamps

## Metadata
- Feature slug: `profile-gamification-stamps`
- Status: in_progress
- Created at: 2026-08-04

## Summary

Пять фич профильной геймификации: кино-паспорт (штампы), бейдж «контр-культ», режиссёрские/франшизные марафоны, полка-физика и Pepe-судья при экстремальных оценках. v1 — только **film-backed rated cards** (inner join `Film`).

## Scope

### Ф13 — Кино-паспорт
- Коллекция штампов на своём профиле (sub-tab **«Коллекция»** в Stats).
- Правила: первая страна, первая оценка десятилетия, 5+ стран в календарном году, N уникальных стран (5/10/20), meta-stamp «первая оценка в году».
- **v2:** штамп «первая ч/б» — не в v1 (нет надёжного metadata).

### Ф14 — Бейдж «контр-культ»
- Медаль на **своих** карточках при расхождении с community avg ≥ 4.0 и `ratings_count >= 3`.
- Surfaces: grid профиля, detail, own FeedCard.

### Ф15 — Режиссёрский / франшизный марафон
- Achievement: 5+ rated cards одному режиссёру (`primary_director_*` из Kinopoisk staff) или одной франшизе (`franchise_key` из sequels_and_prequels).
- UI: рамка полки + chips с drill-down фильтром.

### Ф16 — Полка-физика
- Визуальное состояние полки на **своём** профиле (Оценённые): `neutral` / `slump` (3+ подряд ≤3) / `glow` (3+ подряд ≥9).
- `prefers-reduced-motion` → статичный tint без анимации.

### Ф17 — Pepe-судья
- Frontend-only: случайная фраза Pepe при выборе **1** или **10** в create/edit card flow.
- Срабатывает при пересечении порога (debounce), не спамит при drag.

### Shared infra (v1)
- `Film`: `countries`, `primary_director_kinopoisk_id`, `primary_director_name`, `franchise_key` + Alembic migration.
- Kinopoisk: `GET /v1/staff?filmId=`, `GET /v2.1/films/{id}/sequels_and_prequels`; lazy enrich on resolve + backfill script.
- `GetCatalogCommunityStatsService` → `community_avg_rating`, `is_contrarian` в card DTO.
- `GET /api/me/gamification` → passport, marathons, shelf_physics.

## Acceptance criteria

### Infra
- [ ] Migration + Film columns persisted on Kinopoisk sync/upsert.
- [ ] `EnrichFilmGamificationMetadataService` + `manage_backfill_film_gamification_metadata.py` + `make backfill-film-gamification-metadata`.
- [ ] `GET /api/me/gamification` (auth) returns passport, marathons, shelf_physics.
- [ ] Community stats: avg excludes planned; contrarian at delta ≥ 4.0, count ≥ 3.

### Ф17 Pepe-судья
- [ ] Pools `extreme_rating_low` / `extreme_rating_high` в `microFunCopy.ts`.
- [ ] Hook + UI в create/edit; reduced-motion без анимации; Vitest на threshold crossing.

### Ф16 Полка-физика
- [ ] `ProfileShelfPhysics` wrapper + CSS states на own ProfilePage rated grid.
- [ ] 3 low → slump, 3 high → glow; только свой профиль.

### Ф14 Контр-культ
- [ ] `is_contrarian` в list/detail card API для owner paths.
- [ ] `ContrarianBadge` только на own cards; скрыт при count < 3.

### Ф13 Паспорт
- [ ] `ComputePassportStampsService` + stamp catalog (`passport_stamps.py` / TS mirror).
- [ ] `ProfilePassportPanel` + sub-tab «Коллекция»; locked/unlocked + progress.
- [ ] Public profile: read-only unlocked stamps (`GET /api/users/{id}/gamification/passport`).

### Ф15 Марафоны
- [ ] `ComputeMarathonAchievementsService` (director/franchise, count ≥ 5).
- [ ] `MarathonShelfFrame` + секция в passport panel; games/manual cards excluded.

### Quality
- [ ] Backend pytest: gamification routes, community stats, passport/marathon edge cases.
- [ ] Frontend lint + build pass.
