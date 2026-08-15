# HOT — Cursor session memory
Updated: 2026-08-15T011600Z

Agents: read this file first. Do not glob/read `.cursor/archive/**`. Deep-read `active/`, `memory/logs/`, or `plans/` only for slugs listed below (or named by the user).

## in_progress
1. `profile-heatmap-stats-regroup` — move heatmap to profile; regroup stats sub-tabs (Обзор / Вкус / Сообщество) without losing analytics blocks
   - Feature: `.cursor/features/profile-heatmap-stats-regroup/feature.md`
   - Active: `.cursor/active/profile-heatmap-stats-regroup/`
2. `film-radarr-playback` — rework playback via Prowlarr + Radarr + qBittorrent + Jellyfin (RU 4K prod stack)
   - Feature: `.cursor/features/film-radarr-playback/feature.md`
   - Active: `.cursor/active/film-radarr-playback/`
   - Spec: `docs/superpowers/specs/2026-08-10-film-radarr-torrent-stack-design.md`
3. `collections-core` — curated film collections with rated-only progress tracking
   - Feature: `.cursor/features/collections-core/feature.md`
   - Active: `.cursor/active/collections-core/`
4. `film-award-badges` — Oscar nominee/winner badges on films (independent of collections)
   - Feature: `.cursor/features/film-award-badges/feature.md`
   - Active: `.cursor/active/film-award-badges/`
5. `achievements-rarity-profile-pins` — sticky collection achievements, rarity stats, profile pins
   - Feature: `.cursor/features/achievements-rarity-profile-pins/feature.md`
   - Active: `.cursor/active/achievements-rarity-profile-pins/`
6. `feed-created-sort` — sort feed and profile by completed_at (rated-card creation), not updated_at
   - Feature: `.cursor/features/feed-created-sort/feature.md`
   - Active: `.cursor/active/feed-created-sort/`

## recent_completed
1. `profile-rating-contrast-stats` — closed 2026-08-15T010600Z
   - Feature: `.cursor/features/profile-rating-contrast-stats/feature.md`
   - Active: `.cursor/active/profile-rating-contrast-stats/`
   - Docs: `docs/features/profile-rating-contrast-stats.md`
2. `film-catalog-metadata-ui` — closed 2026-08-15T010500Z
   - Feature: `.cursor/features/film-catalog-metadata-ui/feature.md`
   - Active: `.cursor/active/film-catalog-metadata-ui/`
   - Docs: `docs/features/film-catalog-metadata-ui.md`
3. `tma-watch-open-browser` — closed 2026-08-14T221500Z
   - Feature: `.cursor/features/tma-watch-open-browser/feature.md`
   - Active: `.cursor/active/tma-watch-open-browser/`
   - Docs: `docs/features/tma-watch-open-browser.md`

## evicted (queue for archive)
- `backend-healthcheck` — evicted from recent_completed top-3 on 2026-08-15T010600Z (was #2)
- `film-watch-party` — evicted from recent_completed top-3 on 2026-08-15T010600Z (was #3)
- `film-pleer-playback` — evicted from recent_completed top-3 on 2026-08-14T221500Z (was #3)
- `profile-header-text-metrics` — evicted from recent_completed top-3 on 2026-08-11T023500Z (was #3)
- `profile-stats-people-restructure` — evicted from recent_completed top-3 on 2026-08-11T014500Z (was #3)
- `search-catalog-redesign` — evicted from recent_completed top-3 on 2026-08-10T235000Z (was #3)
- `profile-directors-top20` — evicted from recent_completed top-3 on 2026-08-10T233500Z (was #3)
- `profile-actors-top20` — evicted from recent_completed top-3 on 2026-08-10T224800Z (was #3)
- `standalone-web-telegram-login` — evicted from recent_completed top-3 on 2026-08-10T173000Z (was #3)
- `film-cast-store-all` — evicted from recent_completed top-3 on 2026-08-10T180000Z (was #3)
- `personal-digest-redesign` — evicted from recent_completed top-3 on 2026-08-10T134500Z (was #3)
- `actor-cast-profile-stats` — evicted from recent_completed top-3 on 2026-08-10T120000Z (was #3)
- `profile-streak-stats-legend-ux` — evicted from recent_completed top-3 on 2026-08-10T120000Z (was #3)
- `backend-test-unit-integration-split` — evicted from recent_completed top-3 on 2026-08-08T001000Z (was #3)
- `frontend-refactor-ux-polish` — evicted from recent_completed top-3 on 2026-08-07T232200Z (was #3)
- `feed-post-delete-menu` — evicted from recent_completed top-3 on 2026-08-07T212500Z (was #3)
- `profile-stats-director-franchise` — evicted from recent_completed top-3 on 2026-08-04T123000Z (was #3)
- `cursor-memory-hot-archive` — evicted from recent_completed top-3 on 2026-08-04T170000Z (was #3)
- `tmdb-film-integration` — evicted from recent_completed top-3 on 2026-08-04T111000Z (was #3)
