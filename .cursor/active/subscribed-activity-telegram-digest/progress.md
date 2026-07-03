# Progress: subscribed-activity-telegram-digest

Status: in progress

- Added `SubscribedActivityDigestState` model and migration `x2y3z4a5b678`.
- Implemented candidate collection, weighted selection, Telegram HTML delivery.
- Registered Celery task `tasks.telegram_engagement.send_subscribed_activity_digests`.
- Added pytest coverage for services, tasks, and subscription helper.
- Logged the Celery GC freeze follow-up in `.cursor/memory/logs/2026-07-03T222700Z-subscribed-digest-gc-freeze-code.md`.
- Updated the Celery master bootstrap hook to call `gc.collect()` before `gc.freeze()` and use the requested `freeze_gc_before_worker_fork` signal handler.
