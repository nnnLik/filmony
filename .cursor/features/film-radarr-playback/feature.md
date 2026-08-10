# Film playback via Radarr stack (Prowlarr + qBittorrent + Jellyfin)

## Scope
Replace external balancer HLS (Kodik/Collaps/Alloha) as **primary** playback source with a self-hosted media stack on a **dedicated media node** (not Filmony VPS).

- **Prowlarr** — индексаторы (RU трекеры)
- **Radarr** — библиотека фильмов, профиль **RU 4K**
- **qBittorrent** — загрузка
- **Jellyfin** — стриминг (HLS / direct) для `<video>` в Filmony

Filmony API только оркестрирует (Radarr/Jellyfin HTTP), **не** качает торренты и **не** проксирует видео-байты.

## Acceptance criteria
- Prod media-stack поднят по runbook, Radarr quality profile RU 4K, Prowlarr с RU indexers
- Filmony: «Смотреть» → проверка библиотеки → on-demand add → статус загрузки → воспроизведение через Jellyfin URL
- Ключ фильма: `tmdb_id` (fallback `imdb_id`); `kinopoisk_id` для UI
- Backend tests для orchestration (mock Radarr/Jellyfin)
- Документация: spec + `docs/engineering/media-stack-prod-setup.md`

## Out of scope (v1)
- Sonarr / сериалы
- WebTorrent / magnet в браузере
- Balancer fallback (Kodik…) — код может остаться за feature flag, default OFF
- Filmony-hosted ffmpeg / qBittorrent

## Supersedes
- Primary path from `film-hls-playback` (balancer MVP) — см. spec переработки
