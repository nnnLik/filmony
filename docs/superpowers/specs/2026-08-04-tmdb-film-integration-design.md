# TMDB Film Integration — Design Spec

**Date:** 2026-08-04  
**Status:** draft — awaiting review  
**Feature slug:** `tmdb-film-integration`

---

## 1. Context

Filmony stores films keyed by `kinopoisk_id`. Gamification metadata (countries, primary director, franchise cluster) is fetched from Kinopoisk Unofficial API via up to 3 calls per film. Daily quota is 500 requests — insufficient for backfilling 4020 films (370 of which have user ratings).

TMDB offers generous rate limits (~40 req/10s), rich movie metadata, credits (directors), and collections (franchises). Crosswalk path: Kinopoisk `get_film` already returns `imdbId` → TMDB `GET /3/find/{imdb_id}?external_source=imdb_id`.

---

## 2. Kinopoisk vs TMDB — Field Equivalence Matrix

### 2.1 Core film metadata (resolve path)

| Filmony `Film` field | Kinopoisk source | TMDB source | Equivalent? |
|----------------------|------------------|-------------|-------------|
| `title` | `nameRu` → `nameOriginal` → `nameEn` | `title` (`language=ru-RU`) or `original_title` | **Partial** — RU title may differ |
| `year` | `year` | `release_date[:4]` | **Mostly** |
| `poster_url` | `posterUrl` | `https://image.tmdb.org/t/p/w500{poster_path}` | **Yes** (different CDN) |
| `genres` | `genres[].genre` (RU) | `genres[].name` (`language=ru-RU`) | **Partial** — taxonomy differs |
| `countries` | `countries[].country` | `production_countries[].name` | **Mostly** — naming differs |
| `short_description` | `shortDescription` | first ~500 chars of `overview` | **Partial** |
| `description` | `description` | `overview` | **Partial** |
| `imdb_id` | `imdbId` (DTO only today) | `imdb_id` / find crosswalk | **Yes** |

### 2.2 Gamification metadata (enrichment path)

| Filmony field | Kinopoisk | TMDB | Equivalent? |
|---------------|-----------|------|-------------|
| `primary_director_kinopoisk_id` | first `staff` with `professionKey=DIRECTOR` → `staffId` | **No direct equivalent** | **No** — different ID namespace |
| `primary_director_name` | `nameRu` → `nameEn` from staff | first `crew` with `job=Director` (`language=ru-RU` for name) | **Mostly** — co-directors order may differ |
| `franchise_key` | `kp_franchise:{min(kp_id, sequel_ids)}` | `tmdb_collection:{collection.id}` when `belongs_to_collection` set; else `kp_franchise:{kinopoisk_id}` | **No** — different clustering model |
| `countries` | from `get_film` | from `production_countries` | **Mostly** |

### 2.3 TMDB-only data (store in snapshots)

Persist full responses; normalized extras optional in v1:

- `budget`, `revenue`, `runtime`, `tagline`, `status`
- `belongs_to_collection` (id, name, poster)
- Full `cast` + `crew`
- `production_companies`, `spoken_languages`
- `vote_average`, `vote_count` (TMDB ratings — separate from community ratings)
- External IDs: wikidata, facebook, instagram, twitter
- `backdrop_path`, `homepage`, `origin_country`

---

## 3. Prod diagnostic interpretation

```
Всего фильмов: 4401
Без director/franchise/countries: 4020 (91.3%)
Оценённых без режиссёра: 370
```

- **381 films** (~8.7%) already enriched via Kinopoisk — **must preserve** on backfill.
- **370 rated films** are the highest-priority TMDB backfill target.
- Overlap: rated-without-director ⊆ needs-enrichment — all missing fields correlate (same 4020 set).

**Validation plan:** run comparison script on the ~381 KP-enriched films:

1. Resolve TMDB via stored/new `imdb_id`
2. Compare director **names** (normalized: lowercase, strip punctuation)
3. Compare franchise: for KP `kp_franchise:X`, check if all cluster films share same TMDB `collection.id`
4. Report match rates; manual review bucket for mismatches

Expected outcomes:
- Director names: **~85–95%** match (language/order edge cases)
- Franchise: **lower overlap** — TMDB collections ⊃ KP sequels in many cases (e.g. MCU); KP may link sequels TMDB doesn't cluster and vice versa

---

## 4. Architecture

### 4.1 Data model (`Film` extension)

Follow `Game` pattern (`raw_detail_snapshot`, `detail_synced_at`):

```python
# New columns on film
tmdb_id: int | None                    # unique index
imdb_id: str | None                    # tt1234567, indexed
primary_director_tmdb_id: int | None   # TMDB person id (NEW)
tmdb_detail_snapshot_json: JSON | None  # full GET /3/movie/{id} + append
tmdb_credits_snapshot_json: JSON | None  # if not embedded in detail
tmdb_synced_at: datetime | None
```

Keep existing columns unchanged:
- `primary_director_kinopoisk_id` — set only from Kinopoisk staff (or preserved from prod)
- `franchise_key` — accepts **both** prefixes: `kp_franchise:*` (legacy/KP) and `tmdb_collection:*` (TMDB)

### 4.2 Provider layer

```
backend/src/providers/tmdb/
  tmdb_provider_transport.py
  tmdb_movie_dto.py
  tmdb_credits_dto.py
  tmdb_find_dto.py
  __init__.py
```

Settings:
```python
class TmdbSettings(BaseSettings):
    api_key: str = Field(..., alias='TMDB_API_KEY')
    base_url: str = Field(default='https://api.themoviedb.org/3', alias='TMDB_API_BASE_URL')
    image_base_url: str = Field(default='https://image.tmdb.org/t/p/w500', alias='TMDB_IMAGE_BASE_URL')
    language: str = Field(default='ru-RU', alias='TMDB_LANGUAGE')
```

Auth: `Authorization: Bearer {api_key}` (TMDB v3) or `?api_key=` query param.

Endpoints (2 calls max per film):
1. `GET /find/{imdb_id}?external_source=imdb_id&language=ru-RU`
2. `GET /movie/{tmdb_id}?append_to_response=credits,external_ids&language=ru-RU`

### 4.3 Services

**`SyncFilmFromTmdbService`** — single orchestrator:
- Input: `film: Film`, optional `imdb_id`, optional `tmdb_id`
- Resolve TMDB id via find if needed
- Fetch detail+credits
- Persist snapshots + normalized fields
- Map gamification fields **only if target field is null** (unless `force=True`)

**`EnrichFilmMetadataService`** (refactor or coordinator):
```
1. If imdb_id missing → Kinopoisk get_film (1 KP call) → store imdb_id
2. SyncFilmFromTmdbService (2 TMDB calls)
3. If primary_director_kinopoisk_id still null AND kp_quota_available:
     Kinopoisk staff (1 KP call) — optional, for director page links
```

Replace direct KP staff/sequels in bulk backfill with TMDB path.

### 4.4 Franchise key mapping

```python
def franchise_key_from_tmdb(collection_id: int) -> str:
    return f'tmdb_collection:{collection_id}'

def franchise_key_from_kinopoisk(kp_id: int, sequels: ...) -> str:
    return f'kp_franchise:{min(ids)}'  # existing
```

Update `franchise_label.py`:
- `tmdb_collection:{id}` → lookup collection name from any film's `tmdb_detail_snapshot_json.belongs_to_collection.name`, fallback `Коллекция #{id}`

### 4.5 Director identity (critical)

**Current:** `/directors/{kinopoisk_id}` — Kinopoisk staff ID only.  
**TMDB provides:** person `id` (integer), not compatible with KP staff ID.

**Recommended v1 approach:**

| Field | Source | Used for |
|-------|--------|----------|
| `primary_director_kinopoisk_id` | Kinopoisk staff only | `/directors/{kp_id}` links (existing) |
| `primary_director_tmdb_id` | TMDB credits | New `/directors/tmdb/{tmdb_id}` routes (v1.1) or fallback |
| `primary_director_name` | KP preferred, else TMDB | Display everywhere |

**UI behavior v1:**
- `DirectorChip` links when `primary_director_kinopoisk_id` present (unchanged)
- When only TMDB id + name: show chip **without link** OR link to TMDB person page externally
- v1.1: extend director catalog to index by TMDB id

This preserves prod behavior for 381 enriched films while filling names for 370 rated films immediately.

---

## 5. Backfill strategy

### Script: `manage_backfill_film_tmdb_metadata.py`

```
Priority queue:
1. Films with rated user cards AND missing director/franchise/countries
2. All films missing tmdb_synced_at
3. --force to refresh snapshots

Flags:
--dry-run, --limit N, --sleep 0.25 (TMDB rate limit friendly)
--rated-only (default true for prod first pass)
--skip-kp-staff (default true — don't burn KP quota)
--force-overwrite-gamification (danger: overwrite KP keys)
```

**Quota math:** 2 TMDB requests × 370 rated ≈ 740 requests → ~2 hours at 40/10s (well within limits).

For imdb_id missing: optional 1 KP `get_film` per film (370 KP calls over multiple days) OR manual imdb import batch.

---

## 6. Comparison script

**`manage_compare_kp_tmdb_metadata.py`** — read-only diagnostic:

Input: films where `primary_director_kinopoisk_id IS NOT NULL`  
For each:
1. Fetch/sync TMDB via imdb_id
2. Output CSV/JSON: kp_id, title, kp_director_name, tmdb_director_name, match_bool, kp_franchise_key, tmdb_collection_id, notes

Run on prod (read-only + TMDB calls only) before mass backfill.

---

## 7. Error handling

| Case | Behavior |
|------|----------|
| No imdb_id | Skip TMDB; log; optional KP get_film |
| TMDB find returns 0 movies | Log; leave fields null |
| TMDB find returns TV result | Log; skip (v1 movie-only) |
| Multiple directors | First `job=Director` in crew order (match KP `_first_director`) |
| No collection | Set `franchise_key = kp_franchise:{kinopoisk_id}` (stable singleton, same as KP empty sequels) |
| TMDB 429 | Retry via `shared_async_http` backoff |

---

## 8. Testing

- DTO parsing from fixture JSON (real TMDB responses)
- `SyncFilmFromTmdbService` mapping unit tests
- Backfill selection: rated-first, no overwrite of KP director id
- Franchise label for `tmdb_collection:*` prefix
- Integration test with httpx mock transport

---

## 9. Approaches considered

| Approach | Pros | Cons |
|----------|------|------|
| **A. TMDB enrichment only (recommended)** | KP identity preserved; 2 req/film; fills 370 rated fast | Director links need v1.1 for TMDB ids |
| B. TMDB replaces KP entirely | No KP quota | Loses RU catalog quality; breaks KP-based URLs |
| C. TMDB fallback when KP 402 | Minimal change | Still can't bulk backfill; complex quota tracking |

**Recommendation:** Approach A.

---

## 10. Rollout

1. Migration + provider + SyncFilmFromTmdbService
2. Comparison script → run on prod subset → review match rates
3. Backfill `--rated-only` (370 films)
4. Extend franchise_label + API schemas with `primary_director_tmdb_id`
5. Optional: director routes for TMDB ids (v1.1)
6. Full catalog backfill over subsequent days

---

## 11. Env vars

```
TMDB_API_KEY=...
TMDB_API_BASE_URL=https://api.themoviedb.org/3
TMDB_IMAGE_BASE_URL=https://image.tmdb.org/t/p/w500
TMDB_LANGUAGE=ru-RU
```

CI: placeholder key (mock transport in tests).
