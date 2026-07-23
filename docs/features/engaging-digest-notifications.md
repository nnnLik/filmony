# Engaging Digest Notifications

Redesign of the 48-hour subscribed-activity Telegram digest copy. Cadence, Celery task, and candidate selection are unchanged; only message assembly is richer.

## Behavior

When a digest is sent, the message builder:

1. Computes **window stats** from the scored candidate pool: card/post counts, active authors, average rating, top genres, 9+ count, favorites.
2. Picks a **deterministic intro** (seed: recipient + window start) from variants:
   - genre trend + avg rating
   - high-rating spotlight (2+ cards at 9+)
   - activity pulse (4+ events, 2+ authors)
   - favorites highlight
   - fallback header
3. Renders each selected item with a **kind-specific template**:
   - `new_user_card`: title, year, rating, favorite star, genres, tags, mood-after
   - `high_rating_card`: rating spotlight with genres
   - `new_feed_post`: feed snippet
   - `author_activity_summary`: separate card/post counts

Sparse data falls back to the default intro and minimal item lines (no empty stat lines).

## Key services

- `BuildSubscribedActivityDigestMessageService` — HTML assembly
- `CollectSubscribedActivityDigestCandidatesService` — enriched metadata + tags
- `SendSubscribedActivityTelegramDigestService` — delivery (unchanged cadence)

## Tests

- `backend/src/tests/services/telegram/test_build_subscribed_activity_digest_message.py`
- `backend/src/tests/services/telegram/test_subscribed_activity_digest.py`

Run in Docker:

```bash
make backend-test-one target=src/tests/services/telegram/test_build_subscribed_activity_digest_message.py
make backend-test-one target=src/tests/services/telegram/test_subscribed_activity_digest.py
```

## Related

- Base digest feature: [subscribed-activity-telegram-digest.md](./subscribed-activity-telegram-digest.md)
