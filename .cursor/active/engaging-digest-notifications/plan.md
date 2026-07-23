# Plan: engaging-digest-notifications

1. Add `BuildSubscribedActivityDigestMessageService` with window stats + varied intro/item templates.
2. Extend `DigestCandidate` metadata (genres, tags, rating, moods, activity counts).
3. Enrich collector to populate metadata and load card tags.
4. Wire send service to new builder; keep cadence/selection unchanged.
5. Add unit tests for message builder; extend integration digest test assertions.
6. Publish docs and action log with before/after examples.
