# Action Log

Каждое изменение хранится в отдельном файле в этой директории.

## Правило хранения
- Один файл = одно **milestones**- или **closeout**-действие (не каждый micro-action).
- Формат имени: `YYYY-MM-DDTHHMMSSZ-<feature-slug>-<action-type>.md`.
- Пример: `2026-05-06T053800Z-movie-card-comments-code.md`.
- Индекс `Latest Entries` — **не более 25** ссылок на фрагменты (HOT slugs + newest closeouts). Старые фрагменты остаются на диске; в Phase B уезжают в `.cursor/archive/logs/`.

## Формат записи (внутри файла)
- Timestamp
- Feature slug
- Action type: `plan | code | test | docs | refactor | decision`
- Summary
- Files
- Verification
- Links (опционально)

## Latest Entries
- `2026-08-11T014500Z-film-watch-party-closeout.md`
- `2026-08-11T005500Z-film-pleer-playback-closeout.md`
- `2026-08-10T235000Z-profile-header-text-metrics-closeout.md`
- `2026-08-10T233500Z-profile-stats-people-restructure-closeout.md`
- `2026-08-10T224800Z-film-hls-playback-closeout.md`
- `2026-08-10-search-catalog-redesign-closeout.md`
- `2026-08-10-profile-directors-top20-closeout.md`
- `2026-08-10-profile-actors-top20-closeout.md`
- `2026-08-10-standalone-web-telegram-login-closeout.md`
- `2026-08-10-film-cast-store-all-closeout.md`
- `2026-08-08T001000Z-personal-digest-redesign-closeout.md`
- `2026-08-07T232200Z-actor-cast-profile-stats-closeout.md`
- `2026-08-07T212500Z-profile-streak-stats-legend-ux-closeout.md`
- `2026-08-04T111000Z-backend-test-unit-integration-split-closeout.md`
- `2026-08-04T123000Z-frontend-refactor-ux-polish-closeout.md`
- `2026-08-04T170000Z-feed-post-delete-menu-closeout.md`
- `2026-08-04T160000Z-tmdb-film-integration-closeout.md`
- `2026-08-04T153000Z-profile-stats-director-franchise-closeout.md`
- `2026-08-04T120000Z-cursor-memory-hot-archive-closeout.md`
- `2026-08-04T150000Z-feed-post-edit-unlimited-code.md`
- `2026-08-04T120000Z-social-catalog-slices-abc-code.md`
- `2026-08-04T104900Z-profile-gamification-stamps-docs.md`
- `2026-08-04T095400Z-unlimited-watch-note-code.md`
- `2026-08-04T030800Z-frontend-perf-pass-code.md`
- `2026-08-04T030000Z-social-catalog-slices-d-e-code.md`
- `2026-08-04T024100Z-director-catalog-pages-code.md`
- `2026-08-04T011600Z-offline-feed-cache-code.md`
- `2026-08-04T011600Z-catalog-community-page-code.md`
