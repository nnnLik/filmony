# 005 — Movie rating with tags

## Metadata

| Field | Value |
|--------|--------|
| **Feature slug** | `movie-rating-with-tags` |
| **Priority** | P1 |
| **Target area** | fullstack |
| **Depends on** | [001](./001-telegram-user-base.md), [004](./004-kinopoisk-movie-by-link.md) |
| **Unlocks** | Feed (**007**), comments (**006**), recommendations (**008**), vector updates in Redis |

## Summary

Create a **movie card** (user’s review instance): numeric **rating 1–10**, structured tags (**company**, **mood before**, **mood after** from product enums), and up to **five custom text tags**. This is the core content unit referenced throughout [`.cursor/user-story.md`](../user-story.md) and [`.cursor/tech.md`](../tech.md). Updating a card triggers **user vector** recomputation and **doppelganger** cache refresh (**008**).

## Problem

The product differentiates from Kinopoisk averages by capturing **context**: who you watched with and emotional before/after states, plus free-form tags.

## Backend

### Responsibilities

- Create/update/delete **movie_cards** (or `reviews`) linked to `user_id` + `film_id`; constraint: **one card per user per film** (or explicit versioning — product default: one active row).
- Validate: rating range, enum values, max 5 custom tags, normalization (trim, length).
- **Side effects** (sync or async):
  - Invalidate/update Redis caches for feed, film tops, user vector (**tech.md**).
  - Enqueue Celery: vector recompute, doppelganger similarity refresh.

### Data model (planned)

- **`movie_cards`**: `id`, `user_id`, `film_id`, `rating` (smallint), `company_enum`, `mood_before_enum`, `mood_after_enum`, `created_at`, `updated_at`.
- **`movie_card_tags`**: custom tags (normalized text), max 5 per card.

Enums should match UX labels in [user-story](../user-story.md) (exact lists finalized in implementation).

### API (planned)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/cards` | Create card for `film_id` |
| `PATCH` | `/api/cards/{card_id}` | Update |
| `DELETE` | `/api/cards/{card_id}` | Delete |
| `GET` | `/api/cards/{card_id}` | Detail for owner / public rules |
| `GET` | `/api/films/{film_id}/cards/friends` | Friends’ ratings on this film (ties to **003**) |

### Redis

- User taste vector storage and invalidation per [`.cursor/tech.md`](../tech.md) §5–6.

### Celery

- Tasks: `recompute_user_vector(user_id)`, `invalidate_feed_cache(user_id)`, etc.

### Existing codebase references

| File | Note |
|------|------|
| [`backend/src/api/router.py`](../../backend/src/api/router.py) | Cards router |

### Suggested new modules

- `backend/src/schemas/movie_card.py`
- `backend/src/services/movie_card_service.py`
- `backend/src/services/recommendations/vector.py` — 60/40 weighting rule from tech doc

## Frontend

### Responsibilities

- **Rating form** after film resolve: slider or stepper 1–10.
- **Three structured selectors** (company, mood before, mood after) using Telegram UI components.
- **Custom tags**: chip input, max 5, dedupe case-insensitive if product agrees.
- **Film header** reuse from **004** preview.
- Optional: co-view invite button placeholder for follow-up feature from user-story (API in separate small feature if needed).

### Existing codebase references

| File | Note |
|------|------|
| [`frontend/src/App.tsx`](../../frontend/src/App.tsx) | Future navigation to card screens |

### Suggested new files

- `frontend/src/pages/CreateCardPage.tsx`, `EditCardPage.tsx`
- `frontend/src/components/card/RatingForm.tsx`, `TagChips.tsx`

## Acceptance criteria

- [ ] User can create a card with valid enums and ≤5 custom tags; cannot exceed limits.
- [ ] Duplicate film for same user rejected or upserts per chosen rule (documented).
- [ ] PATCH updates card and triggers backend side effects (vector job enqueued or synchronous per MVP decision).
- [ ] Friends’ ratings for same film retrievable when **003** is present; otherwise endpoint returns empty/friend scope documented.

## Out of scope

- Full invite pipeline “дооценить” — can be a thin follow-up once **003** + notifications (**009**) exist.
- Moderation of custom tag text beyond length limits.

## References

- [`.cursor/tech.md`](../tech.md) — §4–6 (tags, vectors, Celery).
- [`.cursor/user-story.md`](../user-story.md) — шаги 1–3.
- [004](./004-kinopoisk-movie-by-link.md)
