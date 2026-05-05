# 008 — Recommendations via doppelgängers (“двойники”)

## Metadata

| Field | Value |
|--------|--------|
| **Feature slug** | `doppelganger-recommendations` |
| **Priority** | P2 (core differentiator) |
| **Target area** | fullstack |
| **Depends on** | [001](./001-telegram-user-base.md), [005](./005-movie-rating-with-tags.md) |
| **Unlocks** | Stranger inserts in **007**, **009** notification triggers |

## Summary

Maintain a **user taste vector** in **Redis** and a **cached set of doppelgängers** (nearest neighbors by mixed similarity). Similarity formula from [`.cursor/tech.md`](../tech.md): **60%** from rating delta on **shared films**, **40%** from tag overlap (company/mood/custom—weights in implementation). When a high-similarity user rates a film highly, surface recommendations and drive **009** notifications.

## Problem

Average ratings fail for contextual taste; the product promises “двойники” who watch and tag like you, as in [`.cursor/user-story.md`](../user-story.md) (Способ 2).

## Backend

### Responsibilities

- **Vector computation**: on each card create/update/delete, recompute user embedding or sufficient statistics to compare users (exact structure is implementation detail; must support incremental updates).
- **Neighbor search**: top-K users above threshold; store in Redis with TTL; refresh via Celery on schedule or on write amplification threshold.
- **Shared films**: join on `movie_cards` for same `film_id` across users; weight absolute rating difference.
- **Tag overlap**: Jaccard or weighted overlap on enum + custom tags.
- **Recommendation API**: list “films your doppelgängers loved recently” or explain match on film detail.

### Data / infra

- **Redis**: keys per `user_id` for vector + neighbor list; invalidate on new ratings.
- **PostgreSQL**: source of truth for cards; Redis derived.

### API (planned)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/me/doppelgangers` | Top matches with scores (for debug/transparency opt-in) |
| `GET` | `/api/recommendations` | For-you list derived from doppelgänger activity |

### Celery

- `recompute_doppelgangers(user_id)` batch jobs; optional nightly full recompute for drift correction.

### Guardrails

- Exclude users with too few shared films from strong matches; privacy: show **percent match** not raw vector.

### Existing codebase references

| File | Note |
|------|------|
| [`backend/src/conf/settings.py`](../../backend/src/conf/settings.py) | Redis URL, thresholds |

### Suggested new modules

- `backend/src/services/recommendations/similarity.py`
- `backend/src/services/recommendations/doppelganger_store.py` — Redis adapter
- `backend/src/api/recommendations/routes.py`

## Frontend

### Responsibilities

- **Surface**: optional screen or module “Твои двойники” / inline badges on feed items (“совпадение 82%”).
- **Recommendation strip** on home or film pages when API returns suggestions.
- Copy aligned with user-story notification example (names + film).

### Suggested new files

- `frontend/src/pages/RecommendationsPage.tsx`
- `frontend/src/components/recommendations/DoppelgangerBadge.tsx`

## Acceptance criteria

- [ ] After sufficient overlapping activity between two test users, system returns them as mutual or directional neighbors with score ordering.
- [ ] New high rating from neighbor triggers downstream event used by **009** (event hook exists even if notification copy ships later).
- [ ] Recompute completes within acceptable latency strategy (async acceptable).
- [ ] Disabling or too-sparse data yields empty states without errors.

## Out of scope

- Neural collaborative filtering training pipeline.
- Export of raw vectors to clients.

## References

- [`.cursor/tech.md`](../tech.md) — §5–7 (вектор, 60/40, Redis, Celery).
- [`.cursor/user-story.md`](../user-story.md) — Способ 2, уведомление от двойника.
- [005](./005-movie-rating-with-tags.md), [007](./007-feed-friends-and-stranger-inserts.md)
