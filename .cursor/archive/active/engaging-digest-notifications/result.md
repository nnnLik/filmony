# Result: engaging-digest-notifications

Status: **done**

## What was implemented
- New `BuildSubscribedActivityDigestMessageService` assembles digest HTML with:
  - Window-level stats (card/post/author counts, avg rating, top genres, 9+ count, favorites).
  - Deterministic intro variants (genre trend, high-rating spotlight, activity pulse, favorites, fallback).
  - Kind-specific item templates with genres, year, rating, tags, mood-after, activity breakdowns.
- `DigestCandidate` extended with metadata fields; collector loads card tags and tracks card/post counts separately.
- Send service delegates rendering to the new builder; 48h cadence and selection unchanged.

## Before / After examples

### Before
```text
🔔 За последние 48 часов у людей, на которых вы подписаны, появилось интересное:

1. <b>Digest Author</b> опубликовал(а) карточку «Digest Film» с оценкой 10 и добавил(а) её в любимое
2. <b>Digest Author</b> опубликовал(а) пост: «Digest post snippet for followers»
3. ...

Открыть подборку в Filmony
```

### After (rich activity window)
```text
🎭 Тренд: <b>драма</b> (2×), фантастика (1×) · ср. оценка <b>8.5/10</b>

1. 🎬 <b>Аня</b> — «Дюна» (2021) — <b>9/10</b> ⭐
   🎭 фантастика, драма · 🏷 epic · после: кайф

2. 🔥 <b>Макс</b> поставил(а) 9/10 «Интерстellar» · фантастика, драма

3. 💬 <b>Ирина</b> в ленте: «Наконец-то добрался до новой части»

Открыть подборку в Filmony
```

### After (sparse data fallback)
```text
🔔 Подборка за 48 часов от людей, на которых вы подписаны:

1. 💬 <b>Олег</b> в ленте: «Один пост»

Открыть подборку в Filmony
```

## Changed files
- `backend/src/services/telegram/build_subscribed_activity_digest_message.py` (new)
- `backend/src/services/telegram/subscribed_activity_digest_candidates.py`
- `backend/src/services/telegram/send_subscribed_activity_digest.py`
- `backend/src/tests/services/telegram/test_build_subscribed_activity_digest_message.py` (new)
- `backend/src/tests/services/telegram/test_subscribed_activity_digest.py`
- `.cursor/features/engaging-digest-notifications/feature.md`
- `.cursor/active/engaging-digest-notifications/plan.md`
- `.cursor/active/engaging-digest-notifications/progress.md`
- `.cursor/active/engaging-digest-notifications/result.md`
- `docs/features/engaging-digest-notifications.md`

## Verification
```bash
make backend-test-one target=src/tests/services/telegram/test_build_subscribed_activity_digest_message.py
make backend-test-one target=src/tests/services/telegram/test_subscribed_activity_digest.py
```
Both passed in Docker (8 + 6 tests).

## Known limitations
- Intro variant pick is deterministic but not user-configurable.
- Genre labels use raw film.genres strings (no localization layer).
- Window stats computed from digest candidate pool, not a separate analytics query.
