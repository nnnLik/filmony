# Engaging Digest Notifications

Rich copy patterns for subscribed-activity digest items. The standalone 6-hour Telegram digest pipeline (`tasks.telegram_engagement.send_subscribed_activity_digests`) was removed; candidate collection and message templates are reused in the **weekly personal digest** friends block.

## Behavior

When friends-activity items are rendered in the weekly digest, the builder:

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

## Key services (still in use)

- `CollectSubscribedActivityDigestCandidatesService` — enriched metadata + tags (friends section input)
- `BuildPersonalDigestFriendsSectionService` — weekly digest friends block assembly

## Related

- Personal digest: [personal-digest-redesign.md](./personal-digest-redesign.md)
- Base digest feature (historical): [subscribed-activity-telegram-digest.md](./subscribed-activity-telegram-digest.md)
