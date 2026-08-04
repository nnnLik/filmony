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
- `2026-07-29T014500Z-social-depth-pack-controversy-enrich-stored-code.md`
- `2026-07-29T014200Z-pet-project-micro-fun-code.md`
- `2026-07-29T013600Z-social-depth-pack-controversy-tg-upgrade-code.md`
- `2026-07-29T012900Z-frontend-ui-boot-polish-code.md`
- `2026-07-28T174500Z-social-depth-pack-code.md`
- `2026-07-27T151100Z-taste-knowledge-badge-everywhere-test.md`
- `2026-07-27T151000Z-taste-knowledge-badge-everywhere-docs.md`
- `2026-07-27T150300Z-comment-header-actions-overflow-complete.md`
- `2026-07-27T150200Z-comment-header-actions-overflow-docs.md`
- `2026-07-27T142500Z-profile-taste-match-docs.md`
- `2026-07-27T140000Z-backlog-cleanup-decision.md`
- `2026-07-23T180900Z-taste-quiz-guess-rating-docs.md`
- `2026-07-23T180800Z-taste-quiz-guess-rating-frontend-code.md`
- `2026-07-23T180700Z-taste-quiz-guess-rating-code.md`
- `2026-07-23T170000Z-comment-edit-delete-test.md`
