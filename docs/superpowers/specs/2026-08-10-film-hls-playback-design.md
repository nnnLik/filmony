# In-app Film HLS Playback — Design Spec

**Date:** 2026-08-10  
**Status:** approved for implementation  
**Feature slug:** `film-hls-playback`

---

## 1. Context

Filmony today is a social film catalog inside Telegram Mini App (TMA) and standalone web. Users browse films on `FilmDetailPage` (`/films/:filmId`) and manage watchlists, ratings, and community cards — but there is **no in-app playback**. Watching a title requires leaving Filmony to third-party sites or torrent clients.

For a closed beta (~5 users), we need a **minimal viable in-app watch flow**: authenticated users open an HLS stream inside Filmony, without Filmony VPS carrying video bytes and without torrent infrastructure in this phase.

**Catalog anchor:** every `Film` row has a required `kinopoisk_id` (`backend/src/models/film.py`). Playback resolution keys off that id via external balancer APIs (Kodik, Collaps, Alloha). Films without a usable `kinopoisk_id` in API payloads are treated as non-playable in UI.

---

## 2. Product goals

| Goal | Decision |
|------|----------|
| Who can watch | Authenticated users (`CurrentUser`), same as other `/api/films/*` routes |
| Which titles | Films with `kinopoisk_id` that at least one provider can resolve |
| Player | Custom HTML5 `<video>` — **no aggregator iframe**, no embedded partner ads UI |
| Traffic path | Client loads HLS directly from provider CDN; **Filmony server never proxies `.ts` segments** |
| Server transcode | **Out of scope** — no ffmpeg, no qBittorrent, no byte proxy on Filmony VPS |
| Licensing / balancer ToS | Ignored for ~5-user beta; document operational risk only |
| Torrents | **Out of MVP** — magnet / WebTorrent / Jackett / Prowlarr deferred to future phase |

---

## 3. Non-goals (MVP)

- Torrents, magnet links, WebTorrent, Jackett, Prowlarr
- iframe embeds as the primary playback path
- Filmony-hosted stream proxy or segment relay (even “temporary”)
- Watch progress sync, continue watching, resume timestamps
- Offline download
- Serials / season / episode picker UI (contract may carry fields; **movies-only** for MVP)
- Public unauthenticated playback
- Partner ad UI or branded embed chrome

---

## 4. UX

### 4.1 Entry CTA — `FilmDetailPage`

- Route: `/films/:filmId` (`frontend/src/pages/FilmDetailPage.tsx`).
- Add primary CTA **«Смотреть»** at the **top** of the action button stack inside `TitleCommunityDetailLayout` → `watchlistActions` slot (above «Добавить карточку с оценкой» / watchlist controls).
- **Visibility rules:**
  - `auth.kind !== 'ready'` → do not show CTA (existing auth gate).
  - `film.kinopoisk_id` missing, null, or `< 1` → hide CTA entirely (no disabled stub).
  - `kinopoisk_id` present → show enabled «Смотреть» linking to `/films/:filmId/watch`.
- No prefetch of playback URL on detail page — navigation only; resolve happens on watch page (or on first API call there).

### 4.2 Watch page — `FilmWatchPage`

- Route: `/films/:filmId/watch` (new page, fullscreen-ish layout).
- Layout:
  - Top: back control (router back or link to `/films/:filmId`).
  - Center: `<video>` with `playsInline`, `controls`, black letterbox background.
  - Below player (when API returns options): translation picker + quality picker.
  - Title line from API `title` (fallback: film title from catalog if needed for loading shell).
- **Loading:** spinner / `PageLoadingState` while `GET /api/films/{film_id}/playback` runs.
- **Success:** attach stream and autoplay **only after** user tapped «Смотреть» (watch page mount counts as explicit intent; no autoplay from detail page).
- **Empty / error:** full-page or inline message **«Смотреть недоступно»** with short reason when resolve fails (no sources, expired token chain, all providers failed). **Do not** fall back to `openExternalUrl` for playback in MVP — in-app error only. (`openExternalUrl` remains for other features; not used as playback escape hatch.)
- **Re-pick translation/quality:** changing picker re-calls playback API with `translation_id` / `quality` query params and swaps `hls_url`.

### 4.3 Player technology

| Environment | Mechanism |
|-------------|-----------|
| iOS (including TMA on iOS) | Native HLS: set `<video src={hls_url}>` — Safari plays `application/vnd.apple.mpegurl` without hls.js |
| Else (desktop browsers, Android TMA, standalone web) | **hls.js** attached to `<video>` |

**Attributes:** `playsInline`, `controls`, `preload="metadata"`. Optional `crossOrigin="anonymous"` only if a provider CDN requires CORS for hls.js; default omit until proven necessary.

**TMA fullscreen:** iOS inline playback is default. If user requests fullscreen inside TMA, use Telegram viewport API (`expand()`, `requestFullscreen` where supported) — document in implementation; not required for MVP acceptance if inline + `playsInline` works.

### 4.4 Error copy (Russian)

| Condition | User message |
|-----------|--------------|
| 404 film | «Фильм не найден» |
| 422 no sources | «Смотреть недоступно для этого фильма» |
| Network / 5xx | «Не удалось загрузить видео. Попробуйте позже» |
| CDN 403 / decode error after resolve | «Поток недоступен. Попробуйте другую озвучку или качество» |

---

## 5. API

### 5.1 Endpoint

```
GET /api/films/{film_id}/playback
```

- **Auth:** `CurrentUser` dependency (same pattern as `backend/src/api/films/routes.py`).
- **Path:** `film_id` — internal Filmony `Film.id` (integer).
- **Query (optional):**
  - `translation_id` — string, provider-specific translation/voice id
  - `quality` — string, e.g. `360`, `480`, `720`, `1080`

### 5.2 Resolution flow

1. Load `Film` by `film_id`; **404** if missing.
2. Read `film.kinopoisk_id`; if invalid → **422** `playback_unavailable` (defensive; ORM requires id today).
3. Check short-lived server cache (see §7).
4. Run provider chain over **configured** resolvers in order **Kodik → Collaps → Alloha**. A resolver is configured only when its required env vars are set (see §6.3); unconfigured adapters are skipped, not errors.
5. First configured provider returning a valid `PlaybackDescriptor` wins.
6. Map descriptor to JSON; apply `translation_id` / `quality` selection (default: provider’s default or first listed).
7. Return **200** with body below.

### 5.3 Response shape (200)

All field names English in JSON.

```json
{
  "provider": "kodik",
  "title": "Интерстеллар",
  "translations": [
    {
      "id": "t1",
      "label": "Дубляж",
      "is_default": true
    },
    {
      "id": "t2",
      "label": "LostFilm",
      "is_default": false
    }
  ],
  "selected_translation": {
    "id": "t1",
    "label": "Дубляж"
  },
  "qualities": [
    {
      "id": "720",
      "label": "720p",
      "hls_url": "https://cdn.example/.../index.m3u8"
    },
    {
      "id": "1080",
      "label": "1080p",
      "hls_url": "https://cdn.example/.../index.m3u8"
    }
  ],
  "hls_url": "https://cdn.example/.../index.m3u8",
  "expires_at": "2026-08-10T15:30:00Z",
  "film_id": 42,
  "kinopoisk_id": 258687
}
```

| Field | Type | Notes |
|-------|------|-------|
| `provider` | string | `kodik`, `collaps`, `alloha` |
| `title` | string | Display title from provider or film |
| `translations` | array | May be empty for single-track sources |
| `selected_translation` | object \| null | Active translation: matches `translation_id` query when valid; else entry with `is_default: true`; else first in `translations`. `null` only when `translations` is empty |
| `qualities` | array | Each item includes its own `hls_url` when URLs differ per quality |
| `hls_url` | string | Canonical URL for current translation + quality |
| `expires_at` | string (ISO 8601 UTC) | When client should re-resolve; server cache TTL aligned |
| `film_id` | int | Echo |
| `kinopoisk_id` | int | Echo |

**Serials (future):** `season` and `episode` are **not** in the MVP response schema. They will be added when serial playback ships; MVP does not expose episode UI.

### 5.4 Error responses

| Status | When | Body |
|--------|------|------|
| 401 | No / invalid auth | Standard auth error |
| 404 | `film_id` not found | `{ "detail": "film_not_found" }` |
| 422 | Every configured provider returned `None` (no source for this `kinopoisk_id`) | `{ "detail": "playback_unavailable", "message": "Смотреть недоступно для этого фильма" }` |
| 502 | At least one configured provider was attempted and **all** attempts failed with transport/HTTP errors (timeouts, 5xx, parse failures) — none returned a descriptor | `{ "detail": "playback_provider_error" }` |

Empty sources → **422** `playback_unavailable`, not 404. If the chain mixes `None` (no source) and transport errors, **422** when no descriptor was obtained (no-source is the user-visible outcome).

### 5.5 Secrets

- Partner tokens (`KODIK_TOKEN`, `COLLAPS_TOKEN`, `ALLOHA_SECRET`, base URLs) live in **server env only**.
- Never expose tokens, unsigned partner API URLs with secrets, or raw provider JSON to the client.
- Client receives only CDN `hls_url` values already signed or time-limited by the provider.

### 5.6 CDN direct play — risk and MVP mitigation

**Risk:** Provider CDN may enforce Referer, IP binding, or short-lived signed URLs → browser `GET` to `hls_url` returns **403** or stalls even when API resolve succeeded.

**MVP mitigation (explicit):**

1. Multi-provider fallback at **resolve** time: iterate configured resolvers; try the next when the current returns `None` or raises a transport error.
2. Client on fatal media error: show «Поток недоступен…» and let user change translation/quality (re-resolve).
3. **Do not** add Filmony HLS segment proxy in MVP to fix hotlinking.

**Future (out of MVP):** optional same-origin proxy or partner-specific Referer header tricks — only if beta proves CDN blocking is frequent.

---

## 6. Providers

### 6.1 Pluggable resolvers

Location (new):

```
backend/src/providers/playback/
  __init__.py
  base.py              # PlaybackResolver protocol
  kodik_resolver.py
  collaps_resolver.py
  alloha_resolver.py
  dto.py               # PlaybackDescriptor, TranslationDTO, QualityDTO
```

### 6.2 Adapter interface (Python sketch)

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class PlaybackTranslationDTO:
    id: str
    label: str
    is_default: bool = False


@dataclass(frozen=True, slots=True)
class PlaybackQualityDTO:
    id: str
    label: str
    hls_url: str


@dataclass(frozen=True, slots=True)
class PlaybackDescriptor:
    provider: str
    title: str
    translations: tuple[PlaybackTranslationDTO, ...]
    qualities: tuple[PlaybackQualityDTO, ...]
    hls_url: str
    expires_at: datetime
    # Future serials:
    season: int | None = None
    episode: int | None = None


class PlaybackResolver(Protocol):
    provider_name: str

    async def resolve(
        self,
        kinopoisk_id: int,
        translation_id: str | None = None,
        quality: str | None = None,
    ) -> PlaybackDescriptor | None:
        """Return None if this provider has no source for the id."""
        ...
```

### 6.3 Try order

| Order | Provider | Configured when |
|-------|----------|-----------------|
| 1 | Kodik | `KODIK_TOKEN` and `KODIK_API_BASE_URL` both set |
| 2 | Collaps | `COLLAPS_TOKEN` and `COLLAPS_API_BASE_URL` both set |
| 3 | Alloha | `ALLOHA_SECRET` and `ALLOHA_API_BASE_URL` both set |

If no resolver is configured (all env incomplete), treat as **422** `playback_unavailable` — same as all providers returning `None`.

Orchestrator: `ResolveFilmPlaybackService` iterates resolvers; logs provider failures; returns first non-`None` descriptor or raises `PlaybackUnavailable`.

### 6.4 Movies-first

- MVP resolvers query **movie** endpoints by `kinopoisk_id` only.
- `PlaybackDescriptor.season` / `episode` stay `None` for MVP.
- Serial catalog playback is a follow-up: same endpoint, extra query params `season`, `episode`, and serial-aware resolvers — **not** in MVP (§11 Phases 1–3).

---

## 7. Caching

- **Server-side** cache of successful `PlaybackDescriptor` keyed by `(kinopoisk_id, translation_id, quality)`.
- **TTL:** **10 minutes** (within the 5–15 min band; `expires_at` in response = resolve time + 10 min unless provider returns earlier expiry — then use `min(provider_expiry, cache_ttl)`).
- **Storage:** in-process dict with TTL for MVP (single backend worker); Redis optional later if multi-replica.
- **No cache** on hard failures (422 / 502). Negative cache is **out of MVP** (may add later if provider hammering becomes an issue).
- Client may rely on `expires_at` to re-fetch before URL dies; no separate client cache layer required in MVP beyond React state.

---

## 8. Backend architecture

### 8.1 Layers

| Layer | Responsibility |
|-------|----------------|
| `api/films/routes.py` | `GET /{film_id}/playback` — auth, query params, HTTP mapping |
| `services/films/resolve_film_playback.py` | Orchestrator: film load, cache, provider chain, selection |
| `providers/playback/*` | HTTP to partner APIs, parse → `PlaybackDescriptor` |
| `api/films/schemas.py` | `FilmPlaybackResponse` Pydantic models |

### 8.2 Service contract

```python
@dataclass
class ResolveFilmPlaybackService:
    """Resolve HLS playback for a catalog film via external balancers."""

    async def execute(
        self,
        film_id: int,
        viewer_id: int,
        translation_id: str | None = None,
        quality: str | None = None,
    ) -> FilmPlaybackDTO:
        ...

    class FilmNotFound(Exception): ...
    class PlaybackUnavailable(Exception): ...
```

- `FilmPlaybackDTO` is the service-layer return type; `api/films/schemas.py` maps it to `FilmPlaybackResponse` for the HTTP response (same field names as §5.3).
- `viewer_id` used for structured info logs only in MVP (no per-user URL signing).
- Single public `execute`; provider iteration is private.

### 8.3 Settings (env)

```python
KODIK_API_BASE_URL=https://kodikapi.com/search
KODIK_TOKEN=<secret>
COLLAPS_API_BASE_URL=<url>
COLLAPS_TOKEN=<secret>
ALLOHA_API_BASE_URL=<url>
ALLOHA_SECRET=<secret>   # optional pair with ALLOHA_API_BASE_URL — adapter omitted if either missing
PLAYBACK_CACHE_TTL_SECONDS=600
```

---

## 9. Frontend architecture

### 9.1 New artifacts

| Path | Purpose |
|------|---------|
| `frontend/src/pages/FilmWatchPage.tsx` | Watch UI, player, pickers, error states |
| `frontend/src/api/filmPlaybackApi.ts` | `getFilmPlayback(filmId, opts?)` |
| `frontend/src/lib/hlsPlayer.ts` | Thin wrapper: native vs hls.js attach/detach |
| Router entry | `/films/:filmId/watch` → `FilmWatchPage` |

### 9.2 Dependency

- Add **`hls.js`** to `frontend/package.json` (pinned current stable; import only on non-iOS code path).

### 9.3 `FilmDetailPage` changes

- Import `Link` to watch route or `navigate` on button click.
- Render «Смотреть» **first** inside `watchlistActions` fragment when `film.kinopoisk_id >= 1`.

### 9.4 Types (mirror API)

```typescript
export type FilmPlaybackTranslation = {
  id: string
  label: string
  is_default?: boolean
}

export type FilmPlaybackQuality = {
  id: string
  label: string
  hls_url: string
}

export type FilmPlaybackResponse = {
  provider: string
  title: string
  translations: FilmPlaybackTranslation[]
  selected_translation: FilmPlaybackTranslation | null
  qualities: FilmPlaybackQuality[]
  hls_url: string
  expires_at: string
  film_id: number
  kinopoisk_id: number
}
```

### 9.5 iOS detection

Use existing platform helpers if present; otherwise `(/iPad|iPhone|iPod/.test(navigator.userAgent))` for native HLS branch. hls.js **not** loaded on iOS.

---

## 10. Risks and operations

| Risk | Impact | Mitigation in MVP |
|------|--------|-------------------|
| Partner tokens missing / revoked | No playback | Clear 422; ops alert on error rate; env docs in deploy |
| Provider API or domain churn | Resolve failures | Adapter per provider; isolated fixes; fallback chain |
| CDN Referer / IP binding | Play fails after resolve | Next provider at resolve; user switches quality; **no proxy** |
| Telegram Mini App iOS quirks | Inline only, no fullscreen | `playsInline`; viewport API noted for polish |
| Legal / ToS | Account ban on balancer side | Beta scope ~5 users; no Filmony liability engineering in MVP |
| Signed URL expiry | Mid-play stall | `expires_at` + client re-resolve; 10 min cache |

---

## 11. Phased delivery

### Phase 1 — Backend resolver + playback endpoint + tests

- `PlaybackDescriptor` DTOs and Kodik resolver (first provider).
- `ResolveFilmPlaybackService` + `GET /api/films/{film_id}/playback`.
- Env settings and route registration.
- Unit tests: Kodik JSON fixtures → descriptor mapping.
- Integration tests: auth required, 404 film, 422 no sources.

### Phase 2 — Watch page + hls.js + CTA

- `FilmWatchPage`, router, `filmPlaybackApi`.
- `hls.js` integration + iOS native branch.
- «Смотреть» CTA on `FilmDetailPage` with `kinopoisk_id` gate.
- Frontend smoke test: watch route renders; empty/error state when API 422.

### Phase 3 — Multi-provider fallback + cache polish

- Collaps and Alloha adapters.
- Server cache with 10 min TTL and `expires_at` alignment.
- Integration test: primary provider `None` → secondary succeeds.

### Phase 4 — Future (explicitly out of this MVP)

- Magnet / WebTorrent / Jackett fallback when HLS chain fails.
- Serials: season/episode query params and UI.
- Continue watching / progress sync.
- Optional segment proxy if CDN blocking blocks beta.

---

## 12. Testing

### 12.1 Backend unit (`tests/unit/providers/playback/`)

- Each resolver: parse recorded JSON fixtures → `PlaybackDescriptor`.
- Edge cases: empty results, missing `hls_url`, single quality, multiple translations.
- Selection logic: `translation_id` / `quality` picks correct URL from descriptor.

### 12.2 Backend integration (`tests/integration/api/`)

- `test_film_playback_routes.py`:
  - Unauthenticated → 401.
  - Unknown `film_id` → 404.
  - Film exists, all providers mocked empty → 422 `playback_unavailable`.
  - Film exists, all configured providers mocked transport failure → 502 `playback_provider_error`.
  - Happy path with mocked Kodik → 200 and schema fields.
  - Query `translation_id` / `quality` echoed in response.

### 12.3 Frontend

- If Vitest/RTL harness exists: `FilmWatchPage` renders loading → error when API rejects.
- Manual beta checklist: iOS TMA inline play, desktop hls.js, picker swap, back navigation.

### 12.4 Verification commands (Docker)

```bash
make backend-test-one target=src/tests/unit/providers/playback/test_kodik_resolver.py
make backend-test-one target=src/tests/integration/api/test_film_playback_routes.py
cd frontend && npm run lint && npm run build
```

---

## 13. Acceptance criteria (MVP done)

1. Authenticated user with playable film sees «Смотреть» on `/films/:filmId` when `kinopoisk_id` is valid.
2. `/films/:filmId/watch` plays HLS in-app without iframe.
3. No Filmony endpoint proxies video segments.
4. Failed resolve shows «Смотреть недоступно» without opening external browser.
5. Translation and quality pickers work when API returns multiple options.
6. Backend tests cover auth, 404, 422, 502 (all providers transport-fail), and happy path; unit fixture suite passes for each shipped resolver (Kodik in Phase 1; Collaps and Alloha before MVP closeout).

---

## 14. Related files (implementation touch map)

| Area | Path |
|------|------|
| Film model | `backend/src/models/film.py` (`kinopoisk_id`) |
| Film routes | `backend/src/api/films/routes.py` |
| Detail page CTA slot | `frontend/src/pages/FilmDetailPage.tsx` → `watchlistActions` |
| Layout slot | `frontend/src/components/catalog/TitleCommunityDetailLayout.tsx` |
| External URL helper (not for playback) | `frontend/src/lib/openExternalUrl.ts` |
