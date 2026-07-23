# Progress: engaging-digest-notifications

Status: **done**

- Added `build_subscribed_activity_digest_message.py` with window stats, deterministic intro variants, rich item renderers.
- Extended `DigestCandidate` with film/tags/rating/mood/activity metadata.
- Updated collector to load tags and track card/post counts per author.
- Wired `SendSubscribedActivityTelegramDigestService` to new builder.
- Added `test_build_subscribed_activity_digest_message.py`.
