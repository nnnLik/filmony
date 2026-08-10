# Film Watch Party — Design Spec

**Date:** 2026-08-11  
**Status:** decisions locked (2026-08-11) — ready for implementation  
**Feature slug:** `film-watch-party`  
**Builds on:** `film-pleer-playback` (pleer.video iframe)  
**Related (do not merge):** `WatchSession` in social-depth-pack — async co-view after watchlist invite

---

## 1. Context

Filmony has:

| Feature | What it does |
|---------|----------------|
| **Playback** (`film-pleer-playback`) | User opens `/films/:id/watch`, backend resolves `iframe_url`, pleer embed plays |
| **WatchSession** (existing DB) | Created from watchlist «смотрим вместе» invite; status `planned` → participants rate → auto feed post + Telegram nudge |
| **WatchTogetherConfirmSheet** | UI to confirm watchlist invite to friends — **not** live sync |

Users want **смотреть вместе прямо сейчас**: один фильм, общий чат, видно кто смотрит, приглашение по ссылке, синхрон play/pause.

**Hard constraint:** pleer.video runs in a **cross-origin iframe**. Filmony **cannot** call `play()` / `pause()` / `currentTime` inside it. Any «идеальный» sync как у Netflix Party **требует** контролируемого плеера (`<video>` + HLS) — отдельная фаза.

---

## 2. Goals & non-goals

### Goals (MVP phase 1)

| Goal | Decision |
|------|----------|
| Create room | Host from watch page / film page / card page |
| Invite | Share link (TMA deep link + web URL); **any member** can share; optional in-app invite to mutual follows |
| Presence | Roster: in room / away / left; host badge |
| Chat | Text messages in room; persisted for session |
| Playback state | Host authority: playing, paused, `position_ms`, `updated_at` |
| Sync UX (iframe) | Broadcast state + guest UI to align manually or via countdown |
| Auth | Only logged-in users; room join by invite token |
| Server load | No video proxy; small JSON + SSE; fits 8 GB / 4 CPU VPS |

### Non-goals (MVP)

- Public/open rooms without invite
- Anonymous viewers
- Voice/video
- Reactions on timeline (chapter markers)
- Moderation tools beyond host kick
- Multi-film playlist in one party
- Serials / episodes
- Replacing pleer with own CDN in phase 1

---

## 3. Naming (avoid confusion)

| Term | Meaning |
|------|---------|
| **`WatchParty`** (new) | Live room: chat + presence + playback state while watching |
| **`WatchSession`** (existing) | Async: planned co-view → ratings → feed post |
| **Host** | User who created party; only host sends playback commands (MVP) |
| **Guest** | Joined participant |
| **Invite slug** | Unguessable token in URL (`/watch-party/{invite_slug}`) |

Optional later: when party ends, host can «Сохранить как совместный просмотр» → create/link `WatchSession` for rating flow.

---

## 4. User flows

### 4.1 Host starts party

1. User on `/films/:filmId/watch` (or film/card detail → Смотреть).
2. Tap **«Смотреть вместе»** → sheet: title, poster (no guest cap in UI).
3. `POST /api/watch-parties` → resolves playback first; **422** if pleer unavailable; else room created, host redirected to `/watch-party/{invite_slug}`.
4. Same page: iframe player + chat drawer + roster + **«Пригласить»** (any member: copy link, Telegram share).

### 4.2 Guest joins via link

1. Opens `https://app…/watch-party/{invite_slug}` (or TMA start param).
2. If not logged in → login with `returnTo`.
3. `POST /api/watch-parties/{id}/join` → added to roster, SSE connected.
4. Sees player (same `iframe_url` as resolved for `film_id`), chat, host sync bar.

### 4.3 During watch

- Host uses **Filmony transport controls** (not iframe controls): Play / Pause / Seek bar.
- State pushed to server → SSE to all members.
- Guests see: «Ведущий на паузе» / «Перемотка на 42:15» + button **«Синхронизироваться»** (opens hint overlay on iframe: «Нажмите play на …»).
- Chat: side sheet or bottom panel; send with Enter.

### 4.4 Leave / end

- Guest **«Выйти»** → presence `left`; SSE notifies roster.
- Host **«Завершить сеанс»** → room `ended`; all clients toast + redirect to `/films/:id`.
- Idle: no heartbeat 90s → `away`; 30 min away → auto `left`.

### 4.5 Invite channels (MVP)

| Channel | Mechanism |
|---------|-----------|
| Copy link | `invite_url` from API |
| Telegram | `Telegram.WebApp.shareMessage` / `openTelegramLink` with mini-app start param `wp_{invite_slug}` |
| In-app | Pick mutual follows → push notification + deep link (reuse patterns from card share) |

---

## 5. Playback sync — phased strategy

### Phase 1 — **Soft sync** (pleer iframe, ship first)

**Model:** host clock + UI nudges.

```
Host app ──POST playback──► Server ──SSE──► Guest apps
                                │
                         playback_state JSON
```

- Host scrubber is **Filmony UI only** (tracks logical timeline 0…duration if known, else relative ms from party start).
- Guests **do not** auto-control iframe; they see:
  - Banner: «Ведущий: ▶ 01:23:45»
  - **«Синхронизироваться»** — copies host `position_ms` to clipboard / shows «перемотайте плеер на …» (honest UX).
  - Optional **countdown**: host taps «Старт через 3…2…1» → all tap play in iframe together (works surprisingly well for beta).

**Why:** cross-origin iframe blocks programmatic sync; honest MVP beats broken auto-sync.

### Phase 2 — **Hard sync** (custom `<video>` + HLS)

- Replace or supplement pleer with `hls_url` from balancer/Jellyfin.
- Host events → guests apply:

```typescript
targetMs = state.position_ms + (state.playing ? Date.now() - state.updated_at : 0)
if (Math.abs(video.currentTime * 1000 - targetMs) > 2000) video.currentTime = targetMs / 1000
if (state.playing && video.paused) void video.play()
if (!state.playing && !video.paused) video.pause()
```

- Drift correction every 5–10s; seek debounce 300ms on host.

### Phase 3 — **Post-party social**

- «Оценить вместе» → spawn/link `WatchSession`, prefill participants from party roster.

---

## 6. Transport architecture (recommended)

### Option comparison

| Approach | Pros | Cons |
|----------|------|------|
| **WebSocket** | Lowest latency, bidirectional | New infra; sticky sessions or Redis pub/sub for multi-worker |
| **SSE down + REST up** | Matches existing feed SSE; simple auth | Chat/sync via POST; slightly higher latency |
| **Long polling** | Easy | Bad for chat; avoid |

### Recommendation: **SSE + REST** for MVP

Aligns with `global_feed_head_broker` pattern:

```
Client                          Backend
  │ POST /watch-parties/{id}/messages     (chat)
  │ POST /watch-parties/{id}/playback     (host sync)
  │ POST /watch-parties/{id}/heartbeat    (presence, every 30s)
  │ GET  /watch-parties/{id}/events       (SSE, long-lived)
  ▼
  ◄────── data: { type, payload, seq } ──────
```

**Why not WebSocket in v1:** team already ships SSE for feed; one worker MVP disclaimer is acceptable for ~5 beta users. **Phase 1b infra:** in-process broker per party (dict of queues), same limitation documented as feed SSE.

**Scale-out (later):** Redis pub/sub channel `watch_party:{party_id}` → all uvicorn workers forward to local SSE subscribers.

### SSE event envelope

```json
{
  "seq": 42,
  "type": "playback_state | chat_message | presence | party_ended | ping",
  "payload": { }
}
```

- Monotonic `seq` per party for client dedup/reconnect.
- On connect: SSE sends `snapshot` event with full state (roster + last 50 chat + playback_state).

### Reconnect

- Client tracks `last_seq`.
- On reconnect: `GET /events?since_seq=41` or snapshot if gap too large (>500 events — unlikely MVP).

---

## 7. Playback state machine

### State document (authoritative, server)

```json
{
  "playing": true,
  "position_ms": 2534000,
  "updated_at": "2026-08-11T22:15:03.123Z",
  "host_user_id": "uuid",
  "version": 17
}
```

### Host commands

| Command | Effect |
|---------|--------|
| `play` | `playing=true`, bump `updated_at`, keep `position_ms` |
| `pause` | `playing=false`, freeze `position_ms` at scrub time |
| `seek` | set `position_ms`, bump `updated_at` |
| `heartbeat` (while playing) | optional every 10s: update `position_ms` from host client clock |

### Rules

- Only **host** may POST playback mutations (403 otherwise).
- Host transfer: host leaves → prompt assign new host or end party (MVP: **end party**; phase 2: promote longest guest).
- Rate limits: max 10 seeks/min per host; chat 20 msg/min per user.

### Client-side «expected position» (phase 2)

```text
expected_ms = position_ms + (playing ? now - updated_at : 0)
```

---

## 8. Chat

### MVP

- Text only, max 500 chars, UTF-8.
- Stored in `watch_party_message` table.
- SSE `chat_message` event on insert.
- No threads, no edits (MVP); delete own message within 2 min.

### Optional v1.1

- System messages: «Иван присоединился», «Ведущий поставил на паузу».
- Emoji quick reactions (not synced to timeline).

### Not in scope

- Images, stickers, @mentions (can reuse comment mention later).

---

## 9. Presence & roster

### Member states

| Status | Meaning |
|--------|---------|
| `active` | SSE connected + heartbeat < 90s |
| `away` | heartbeat missed |
| `left` | explicit leave or timeout |

### Roster payload

```json
{
  "members": [
    {
      "user_id": "uuid",
      "display_name": "…",
      "photo_url": "…",
      "role": "host | guest",
      "status": "active",
      "joined_at": "…"
    }
  ]
}
```

UI: avatars row under header; host crown icon.

---

## 10. Security & privacy

| Topic | Rule |
|-------|------|
| Invite slug | `secrets.token_urlsafe(16)` — unguessable |
| Join | Must be authenticated; optional `allowed_user_ids` if invite targeted |
| Room cap | **No product cap** on party size; server hard limit `WATCH_PARTY_HARD_MAX_MEMBERS` (default **64**, abuse guard only) |
| Create guard | **Reject** party if `GET playback` would return `playback_unavailable` for `film_id` |
| One active party / user | **Yes** — user cannot create or join another party while `active` member elsewhere |
| Kick | Host can remove guest (MVP) |
| Expiry | Party `active` max 12h; then auto `ended` |
| iframe_url | Resolved server-side; same as solo playback; not user-supplied |
| XSS | Chat sanitized same as comments (plain text) |

---

## 11. API sketch

### REST

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/watch-parties` | Create party `{ film_id }` → `{ id, invite_slug, invite_url }` |
| `GET` | `/api/watch-parties/{id}` | Snapshot (film, playback iframe_url, roster, playback_state) |
| `POST` | `/api/watch-parties/{id}/join` | Join roster |
| `POST` | `/api/watch-parties/{id}/leave` | Leave |
| `POST` | `/api/watch-parties/{id}/end` | Host ends party |
| `POST` | `/api/watch-parties/{id}/playback` | Host: `{ action: play\|pause\|seek, position_ms? }` |
| `GET` | `/api/watch-parties/{id}/messages?cursor=` | Chat history page |
| `POST` | `/api/watch-parties/{id}/messages` | `{ body }` |
| `POST` | `/api/watch-parties/{id}/heartbeat` | Presence ping |
| `GET` | `/api/watch-parties/by-slug/{invite_slug}` | Resolve slug → party id (for join landing) |

### SSE

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/watch-parties/{id}/events` | `text/event-stream`; auth required; member only |

### Resolve by slug route

Join landing: `/watch-party/:inviteSlug` frontend route → `GET by-slug` → join flow.

---

## 12. Data model (new tables)

### `watch_party`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `invite_slug` | str unique | URL token |
| `host_user_id` | UUID FK user | |
| `film_id` | int FK film | |
| `playback_iframe_url` | str | snapshot at create from resolver |
| `status` | enum | `active`, `ended` |
| `max_members` | int nullable | **NULL** = unlimited in product; enforce `WATCH_PARTY_HARD_MAX_MEMBERS` on join only |
| `playback_state` | JSONB | authoritative state doc |
| `created_at` / `ended_at` | timestamptz | |

### `watch_party_member`

| Column | Type |
|--------|------|
| `party_id` | UUID FK |
| `user_id` | UUID FK |
| `role` | host / guest |
| `status` | active / away / left |
| `last_seen_at` | timestamptz |
| PK | (party_id, user_id) |

### `watch_party_message`

| Column | Type |
|--------|------|
| `id` | bigint PK |
| `party_id` | UUID FK |
| `author_user_id` | UUID FK |
| `body` | text |
| `created_at` | timestamptz |

Index: `(party_id, id)` for chat pagination.

**Do not** extend `WatchSession` for live state — different lifecycle.

---

## 13. Frontend routes & UI

| Route | Page |
|-------|------|
| `/watch-party/:inviteSlug` | `WatchPartyPage` — player + chat + roster |
| Entry | «Смотреть вместе» on `FilmWatchPage`, `FilmDetailPage`, `MovieCardDetailPage` |

### Layout (mobile-first)

```
┌─────────────────────────────┐
│ ←  Интерстellar    👥 3  🔗 │
├─────────────────────────────┤
│                             │
│      iframe / player        │
│                             │
├─────────────────────────────┤
│ Host controls (if host)     │
│ ▶  ────●──────  1:23:45     │
│ [ Старт 3-2-1 ]             │
├─────────────────────────────┤
│ Sync hint (guest)           │
├─────────────────────────────┤
│ Chat (expandable sheet)     │
└─────────────────────────────┘
```

- Reuse `WatchTogetherConfirmSheet` visual language for create flow (different API).
- Telegram: if iframe broken → «Открыть в браузере» + party still works for chat/sync.

---

## 14. Telegram Mini App

| Issue | Mitigation |
|-------|------------|
| iframe blocked | External browser button; chat/sync still in TMA |
| Share invite | `shareMessage` with start param `wp_{slug}` |
| Background | SSE disconnect → `away`; reconnect on focus |
| Back button | `navigate(-1)`; leaving party triggers `leave` API |

Parse start param in existing `TelegramMiniAppStartParamRedirect`.

---

## 15. VPS / infra budget

| Resource | Estimate (1 active party, ~10 users) |
|----------|-------------------------------------|
| RAM | +negligible vs Postgres rows + SSE connections |
| CPU | SSE + JSON; no transcoding |
| Bandwidth | Chat + events only; video still pleer CDN |
| Connections | 1 SSE per member; cap concurrent parties via env |

Env:

```env
WATCH_PARTY_HARD_MAX_MEMBERS=64
WATCH_PARTY_MAX_ACTIVE_PER_USER=1
WATCH_PARTY_TTL_HOURS=12
WATCH_PARTY_SSE_PING_SECONDS=25
```

---

## 16. Testing

| Layer | Coverage |
|-------|----------|
| Unit | Playback state transitions; slug generation; rate limits |
| Integration | Create/join/end; host-only playback; SSE receives event after POST |
| Frontend | WatchPartyPage join flow; reconnect snapshot (vitest + MSW) |

---

## 17. Implementation phases

| Phase | Deliverable |
|-------|-------------|
| **1a** | DB + create/join/get/end REST + by-slug |
| **1b** | SSE broker + playback POST + chat POST/GET |
| **1c** | `WatchPartyPage` UI + invite share |
| **1d** | Entry CTAs on watch/film/card pages |
| **2** | Custom `<video>` hard sync (optional pleer fallback) |
| **3** | End party → `WatchSession` + rating nudge |

---

## 18. Locked product decisions (2026-08-11)

| # | Question | Decision |
|---|----------|----------|
| 1 | Max party size | **Без лимита в продукте**; только server hard cap 64 (env) против злоупотреблений |
| 2 | Who can invite | **Любой участник** комнаты (host и guest) — share link / Telegram |
| 3 | No playback on pleer | **Да** — нельзя создать party; join тоже проверяет, что `iframe_url` ещё валиден |
| 4 | One active party per user | **Да** — вторую комнату создать/войти нельзя, пока пользователь `active` в другой |
| 5 | Chat moderation (host delete any) | *Open — default MVP: delete own only* |

Implementation notes for #4:

- Before `POST /api/watch-parties`: reject if viewer already `active` in any party.
- Before `POST …/join`: same check + return **409** `already_in_active_party` with `{ active_party_id, invite_slug }` so UI can offer «перейти в текущую комнату».

Implementation notes for #3:

- `CreateWatchPartyService` calls `ResolveFilmPlaybackService` first; propagate `PlaybackUnavailable` → HTTP **422** `playback_unavailable`.
- Store `playback_iframe_url` + `playback_expires_at` on party row; on join, re-resolve if expired.

---

## 19. Risks

| Risk | Mitigation |
|------|------------|
| iframe sync frustration | Clear copy; countdown sync; phase 2 player |
| SSE multi-worker | Document MVP single-worker; Redis pub/sub before scale |
| pleer URL expiry | Re-resolve on party join if `expires_at` passed |
| Abuse in chat | Rate limit + report (later) |

---

## 20. References

- Playback: `docs/features/film-pleer-playback.md`
- Async co-view: `docs/features/social-depth-pack.md` (`WatchSession`)
- SSE pattern: `backend/src/services/feed/global_feed_head_broker.py`
- UI sheet: `frontend/src/components/watchlist/WatchTogetherConfirmSheet.tsx`
