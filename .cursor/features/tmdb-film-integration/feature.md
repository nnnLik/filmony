# TMDB film integration

## Problem

Kinopoisk Unofficial API daily quota (500 req/day) blocks bulk enrichment of director, franchise, and countries metadata. On prod (2026-08-04): 4401 films, 91.3% missing gamification metadata; 370 rated films without director/franchise.

## Goal

Integrate TMDB as a **secondary enrichment source** that pulls and persists **full movie metadata** locally, while keeping Kinopoisk as the primary catalog identity (`kinopoisk_id`).

## Scope

### In scope

- TMDB provider transport + DTOs (mirror `providers/rawg/` / `providers/kinopoisk/` patterns)
- Persist `tmdb_id`, `imdb_id`, normalized fields, and full JSON snapshots on `Film` (pattern: `Game.raw_detail_snapshot`)
- Enrichment service: TMDB via IMDB crosswalk (`GET /3/find/{imdb_id}?external_source=imdb_id` + `GET /3/movie/{id}?append_to_response=credits,external_ids`)
- Map TMDB → existing `Film` gamification fields where semantically equivalent
- Backfill script for rated films first, then full catalog
- Comparison/diagnostic script: TMDB vs Kinopoisk on already-enriched prod subset (~381 films)
- Do **not** overwrite existing KP-sourced director/franchise unless `--force`

### Out of scope (v1)

- Replace Kinopoisk search/resolve as primary catalog source
- TMDB search in mixed catalog candidates
- TV series / Kinopoisk `serial` handling via TMDB TV API

## Acceptance criteria

1. `Film` stores `tmdb_id`, `imdb_id`, and full TMDB detail + credits JSON snapshots with sync timestamp.
2. Enrichment fills `countries`, `primary_director_name`, `franchise_key` from TMDB when KP data absent.
3. Existing 381 KP-enriched films unchanged by default backfill (no regression).
4. Diagnostic script reports director name match rate and franchise cluster overlap between KP and TMDB on enriched subset.
5. Rated films without metadata (370) can be backfilled without Kinopoisk staff/sequels API calls.
6. pytest coverage for transport, DTO parsing, enrichment mapping, and backfill selection logic.

## Open decision

**Director page identity:** TMDB person IDs ≠ Kinopoisk staff IDs. See design doc § Director identity.
