# HOT — Cursor session memory
Updated: 2026-08-10T235000Z

Agents: read this file first. Do not glob/read `.cursor/archive/**`. Deep-read `active/`, `memory/logs/`, or `plans/` only for slugs listed below (or named by the user).

## in_progress
1. `film-radarr-playback` — rework playback via Prowlarr + Radarr + qBittorrent + Jellyfin (RU 4K prod stack)
   - Feature: `.cursor/features/film-radarr-playback/feature.md`
   - Active: `.cursor/active/film-radarr-playback/`
   - Spec: `docs/superpowers/specs/2026-08-10-film-radarr-torrent-stack-design.md`
2. `collections-core` — curated film collections with rated-only progress tracking
   - Feature: `.cursor/features/collections-core/feature.md`
   - Active: `.cursor/active/collections-core/`
3. `film-award-badges` — Oscar nominee/winner badges on films (independent of collections)
   - Feature: `.cursor/features/film-award-badges/feature.md`
   - Active: `.cursor/active/film-award-badges/`
4. `achievements-rarity-profile-pins` — sticky collection achievements, rarity stats, profile pins
   - Feature: `.cursor/features/achievements-rarity-profile-pins/feature.md`
   - Active: `.cursor/active/achievements-rarity-profile-pins/`

## recent_completed
1. `profile-header-text-metrics` — closed 2026-08-10T235000Z
   - Feature: `.cursor/features/profile-header-text-metrics/feature.md`
   - Active: `.cursor/active/profile-header-text-metrics/`
   - Docs: `docs/features/profile-header-text-metrics.md`
2. `profile-stats-people-restructure` — closed 2026-08-10T233500Z
   - Feature: `.cursor/features/profile-stats-people-restructure/feature.md`
   - Active: `.cursor/active/profile-stats-people-restructure/`
   - Docs: `docs/features/profile-stats-people-restructure.md`
3. `film-hls-playback` — closed 2026-08-10T224800Z
   - Feature: `.cursor/features/film-hls-playback/feature.md`
   - Active: `.cursor/active/film-hls-playback/`
   - Docs: `docs/features/film-hls-playback.md`

## evicted (queue for archive)
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
