# Media stack prod setup — Prowlarr + Radarr + qBittorrent + Jellyfin

Runbook для **отдельного media node** (не Filmony VPS). Цель: **русские релизы, приоритет 4K**, библиотека готова к интеграции с Filmony (`PLAYBACK_MODE=radarr`).

**Design spec:** [`docs/superpowers/specs/2026-08-10-film-radarr-torrent-stack-design.md`](../superpowers/specs/2026-08-10-film-radarr-torrent-stack-design.md)

---

## 0. Prerequisites

| Item | Requirement |
|------|-------------|
| Host | Linux, ≥ 4 CPU, ≥ 8 GB RAM, **≥ 2 TB** disk for `/mnt/media` |
| Docker + Compose v2 | Installed |
| Network | Stable; Filmony backend reaches media node (Tailscale/LAN) |
| Indexer accounts | RuTracker (and backups) credentials ready |
| Domain (optional) | `jellyfin.yourdomain` + TLS if not Tailscale-only |

Filmony VPS **не** запускает этот compose.

---

## 1. Directory layout on media node

```bash
sudo mkdir -p /mnt/media/{movies,downloads,config/{prowlarr,radarr,qbittorrent,jellyfin}}
sudo chown -R 1000:1000 /mnt/media
```

| Path | Purpose |
|------|---------|
| `/mnt/media/movies` | Radarr root folder + Jellyfin library |
| `/mnt/media/downloads` | qBittorrent incomplete/complete |
| `/mnt/media/config/*` | Persistent app config |

---

## 2. Docker Compose (reference)

Create on media node (implementation phase adds this to repo as `media-stack/docker-compose.yml`):

```yaml
services:
  prowlarr:
    image: lscr.io/linuxserver/prowlarr:latest
    container_name: prowlarr
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Moscow
    volumes:
      - /mnt/media/config/prowlarr:/config
    ports:
      - "9696:9696"
    restart: unless-stopped

  radarr:
    image: lscr.io/linuxserver/radarr:latest
    container_name: radarr
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Moscow
    volumes:
      - /mnt/media/config/radarr:/config
      - /mnt/media/movies:/movies
      - /mnt/media/downloads:/downloads
    ports:
      - "7878:7878"
    restart: unless-stopped

  qbittorrent:
    image: lscr.io/linuxserver/qbittorrent:latest
    container_name: qbittorrent
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Moscow
      - WEBUI_PORT=8080
    volumes:
      - /mnt/media/config/qbittorrent:/config
      - /mnt/media/downloads:/downloads
    ports:
      - "8080:8080"
      - "6881:6881"
      - "6881:6881/udp"
    restart: unless-stopped

  jellyfin:
    image: jellyfin/jellyfin:latest
    container_name: jellyfin
    environment:
      - TZ=Europe/Moscow
    volumes:
      - /mnt/media/config/jellyfin:/config
      - /mnt/media/movies:/media/movies:ro
    ports:
      - "8096:8096"
    restart: unless-stopped
```

```bash
docker compose up -d
```

---

## 3. qBittorrent (first-time)

1. Open `http://<media-ip>:8080` — default login often `admin` / `adminadmin` (change immediately).
2. **Tools → Options → Downloads**
   - Default save path: `/downloads`
   - Keep incomplete in: `/downloads/incomplete`
3. **Categories:** create `radarr` (Radarr will use it automatically when linked).
4. Note credentials for Radarr download client setup.

---

## 4. Prowlarr

1. Open `http://<media-ip>:9696`
2. **Settings → General** — note API key (`PROWLARR_API_KEY`)
3. **Indexers → Add**
   - **RuTracker** (Cardigann/custom — follow current Prowlarr indexer definition)
   - Add credentials / cookies per indexer docs
   - Test → green check
   - Add backup indexers (Rutor, etc.)
4. **Apps → Radarr**
   - Add Radarr instance: `http://radarr:7878` (or `http://127.0.0.1:7878`)
   - Radarr API key (from step 5)
   - Sync Level: **Full** or **Add and Remove**
   - Sync indexers → **Sync**

Verify: Radarr → Settings → Indexers shows Prowlarr-synced indexers.

---

## 5. Radarr

1. Open `http://<media-ip>:7878`
2. **Settings → General → Security** — copy API key (`RADARR_API_KEY`)
3. **Media Management → Root Folders**
   - Add `/movies`
4. **Settings → Download Clients → Add → qBittorrent**
   - Host: `qbittorrent` (docker network) or `127.0.0.1`
   - Port: `8080`
   - Username/password from step 3
   - Category: `radarr`
   - **Remote path mapping** if needed:
     - Remote: `/downloads`
     - Local: `/downloads`
5. **Settings → Media Management**
   - Rename movies: **Yes**
   - Replace illegal chars: Yes

### 5.1 Quality profile «RU-2160p»

**Settings → Profiles → Quality Profiles → Add**

1. Name: `RU-2160p`
2. Enable qualities (upward priority):
   - Bluray-2160p
   - WEBRip-2160p
   - WEBDL-2160p
   - Bluray-1080p (fallback)
3. Cutoff: **Bluray-2160p** or **WEBRip-2160p**

### 5.2 Custom formats (Russian audio)

**Settings → Custom Formats → Add**

Example rules (adjust regex to your scene):

| Name | Implementation |
|------|----------------|
| `Language: Russian` | Language spec Russian → Score **+10000** |
| `Russian dub markers` | Release title regex `(?i)(dub|dubbed|дубляж|пифагор|movie dub)` → **+500** |
| `English only` | Language English, not multi → **-10000** |

Apply custom formats to profile **RU-2160p** with **Minimum Custom Format Score** e.g. **5000** (forces RU track).

### 5.3 Release profile

- Prefer repacks/propers  
- Required: reject cam/ts if possible via custom format negative scores

Set **RU-2160p** as default quality profile for new movies.

---

## 6. Jellyfin

1. Open `http://<media-ip>:8096` — complete setup wizard
2. Create admin user; create **service user** `filmony-playback` (optional separate from admin)
3. **Dashboard → API** — create API key (`JELLYFIN_API_KEY`)
4. **Libraries → Add → Movies**
   - Folder: `/media/movies`
   - Metadata: TMDB (preferred for Filmony mapping)
5. **Playback → Transcoding**
   - Enable hardware acceleration if GPU available (Intel QSV / NVENC)
   - For remote/TMA clients: allow HLS; max streaming bitrate 20–40 Mbps for 4K LAN, lower for internet

Note `JELLYFIN_USER_ID` for API stream calls (Dashboard → user → copy id).

---

## 7. Manual smoke test (before Filmony)

1. Radarr → **Add movie** → search «Interstellar» / TMDB 157336
2. Quality profile: **RU-2160p**
3. Monitor: Yes, Search on add: Yes
4. Wait for qBittorrent to finish → Radarr shows **Downloaded**
5. Jellyfin → scan library → play movie with **Russian audio** and **2160p** (or transcoded HLS)

**Pass criteria:** playback in Jellyfin with RU audio; file on disk under `/mnt/media/movies/...`.

Repeat with one more title to validate indexer stability.

---

## 8. Connect Filmony backend (after Phase 1 code)

In `vars/.env.production` on **Filmony VPS**:

```env
PLAYBACK_MODE=radarr
PLAYBACK_BALANCER_ENABLED=false

RADARR_BASE_URL=http://100.x.x.x:7878
RADARR_API_KEY=...

JELLYFIN_BASE_URL=https://jellyfin.yourdomain
JELLYFIN_API_KEY=...
JELLYFIN_USER_ID=...

PLAYBACK_CACHE_TTL_SECONDS=60
```

Use Tailscale IP or private LAN — **do not expose Radarr port 7878 to public internet**.

Restart Filmony backend.

Test:

```bash
curl -H "Authorization: Bearer <token>" \
  "https://filmony-api.example/api/films/<film_id>/playback"
```

---

## 9. Security checklist

- [ ] Changed qBittorrent default password
- [ ] Radarr/Prowlarr API keys rotated; not in git
- [ ] UFW: only Tailscale/LAN ports open (7878, 8096, 9696 not public)
- [ ] Jellyfin behind HTTPS reverse proxy if public
- [ ] Filmony uses read-only Jellyfin API key where possible

---

## 10. Prod sign-off checklist

- [ ] Prowlarr: all indexers green
- [ ] Radarr: download client test OK
- [ ] Quality profile RU-2160p default
- [ ] ≥ 2 reference films in library (RU audio, 4K or documented 1080p fallback)
- [ ] Jellyfin HLS plays on iOS Safari (TMA test device)
- [ ] Jellyfin HLS plays on desktop Chrome (hls.js path)
- [ ] Disk usage alert configured (< 100 GB free warning)
- [ ] Filmony integration curl returns `ready` + `hls_url`

---

## 11. Troubleshooting

| Symptom | Check |
|---------|-------|
| Radarr search empty | Prowlarr indexer test; credentials; category caps |
| qBittorrent stalled | Port 6881 forwarded? Seeds? |
| Wrong language | Custom format scores; manual import language in Radarr |
| Jellyfin no item | Library scan path; file permissions PUID 1000 |
| Filmony 502 | Network Filmony→media node; API keys; firewall |
| TMA won't play 4K | Jellyfin transcode to 1080p HLS; check client codec |

---

## 12. Maintenance

- Weekly: Prowlarr indexer health
- Monthly: disk space; Radarr queue cleanup
- Backup: `/mnt/media/config/{radarr,prowlarr,jellyfin}` (not full movie library if re-download acceptable)

---

## Related

- Feature spec: [`docs/superpowers/specs/2026-08-10-film-radarr-torrent-stack-design.md`](../superpowers/specs/2026-08-10-film-radarr-torrent-stack-design.md)
- Previous balancer approach: [`docs/features/film-hls-playback.md`](../features/film-hls-playback.md) (deprecated primary)
