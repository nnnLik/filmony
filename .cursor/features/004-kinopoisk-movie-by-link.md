# 004 — Add movie by Kinopoisk link

## Metadata

| Field | Value |
|--------|--------|
| **Feature slug** | `kinopoisk-movie-by-link` |
| **Priority** | P1 |
| **Target area** | fullstack |
| **Depends on** | [001](./001-telegram-user-base.md) |
| **Unlocks** | **005** (rating cards need canonical film entity) |

## Summary

Users paste a **Kinopoisk URL**; the system resolves a **canonical film record** (title, year, poster, external kp id) via **Kinopoisk API Unofficial** (per [`.cursor/tech.md`](../tech.md)), stores it in PostgreSQL, and returns it to the client for the rating flow. Parsing/runtime work may be delegated to **Celery** for resilience.

## Problem

Manual film entry is friction; the product promises: “Кидаешь ссылку на Кинопоиск — сервис сам подтянет название и картинку” ([`.cursor/user-story.md`](../user-story.md)).

## Backend

### Responsibilities

- **Parse** Kinopoisk URLs (film page variants, query params, mobile URLs) → extract **film id**.
- **Fetch metadata** from Kinopoisk API Unofficial: title, original title, year, poster URL, kinopoisk id, possibly genres/runtime for future filters.
- **Upsert `films`** table: unique by `kinopoisk_id` (or chosen external key).
- **Idempotency**: same link twice returns same internal `film_id`.
- **Rate limits / failures**: structured errors; optional async job with polling endpoint if API is slow (align with Celery section in [`.cursor/tech.md`](../tech.md)).

### Data model (planned)

- Table **`films`**: `id`, `kinopoisk_id`, `title`, `year`, `poster_url`, raw metadata JSON optional, `created_at`.

### API (planned)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/films/resolve` | Body: `{ "url": "https://www.kinopoisk.ru/film/..." }` → film payload |
| `GET` | `/api/films/{film_id}` | Cached film details |

### Configuration

- Extend [`backend/src/conf/settings.py`](../../backend/src/conf/settings.py): `KINOPOISK_API_KEY` / base URL / timeout per unofficial API docs.

### Celery

- Task `resolve_kinopoisk_film(url)` for retries and offloading; store job id if async pattern is used.

### Existing codebase references

| File | Note |
|------|------|
| [`backend/src/conf/settings.py`](../../backend/src/conf/settings.py) | Add Kinopoisk-related settings |
| [`backend/src/api/router.py`](../../backend/src/api/router.py) | Register films router |

### Suggested new modules

- `backend/src/services/kinopoisk/client.py` — HTTP client.
- `backend/src/services/kinopoisk/parse_url.py` — URL → id.
- `backend/src/api/films/routes.py`

## Frontend

### Responsibilities

- **“Добавить фильм”** flow: paste field, validate non-empty URL, call `POST /api/films/resolve`, show **preview** (poster, title, year).
- On success, transition to **005** rating form with `film_id` prefilled.
- Error states: invalid URL, film not found, API timeout.

### Existing codebase references

| File | Note |
|------|------|
| [`frontend/vite.config.ts`](../../frontend/vite.config.ts) | `/api` proxy for dev |

### Suggested new files

- `frontend/src/pages/AddFilmPage.tsx`
- `frontend/src/components/film/FilmPreviewCard.tsx`

## Acceptance criteria

- [ ] Valid Kinopoisk film URL returns stable `film_id` and consistent metadata.
- [ ] Same URL / same kp id does not duplicate DB rows.
- [ ] Invalid URL returns 422 with clear message.
- [ ] Poster and title display in UI preview match API payload.
- [ ] Secrets for Kinopoisk client live in env, not in repo.

## Out of scope

- Importing full cast/crew graph (unless needed later).
- Non-Kinopoisk sources.

## References

- [`.cursor/tech.md`](../tech.md) — Celery, Kinopoisk API Unofficial.
- [001](./001-telegram-user-base.md)
