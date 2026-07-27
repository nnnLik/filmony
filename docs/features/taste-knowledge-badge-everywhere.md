# Taste Knowledge Badge Everywhere

## Overview

Taste-quiz **accuracy %** appears next to other users across the app. The number answers: **how well do I know their taste?** — the authenticated viewer is the guesser; the shown user is the owner.

This is separate from [profile taste match](./profile-taste-match.md) (Jaccard film overlap in profile stats).

## Behavior

- Show `(N%)` only when the viewer has **≥ 1 attempt** against that owner.
- Hide badge when the shown user is the viewer (own comments / self rows).
- Batch-fetch up to **100** unique owner ids per screen via one React Query call.

## API

`POST /api/taste-quiz/knowledge/batch-as-guesser`

```json
{ "owner_user_ids": ["uuid", "..."] }
```

Response `items`: owner id → `{ attempts, accuracy_pct, points_sum }`. Omits self and owners with zero attempts.

## Frontend

- **Hook:** `frontend/src/hooks/useTasteQuizKnowledgeOfUsers.ts` → `knowledgeByOwnerId`
- **Badge:** `TasteQuizCommentAuthorBadge` / `TasteQuizKnowledgeBadge`
- **Surfaces:** feed cards, comment threads, film detail community list, subscriptions, search users, public profile

## Backend

- **Service:** `BatchTasteQuizKnowledgeAsGuesserService` (`backend/src/services/taste_quiz/batch_knowledge_as_guesser.py`)

## Verification

| Check | Command | Result |
|-------|---------|--------|
| Backend pytest | `make backend-test-one target=src/tests/api/test_taste_quiz_routes.py::test_knowledge_batch_as_guesser_omits_zero_attempts_and_self` | passed |
| Frontend lint | `cd frontend && npm run lint` | exit 0 |
| Frontend build | `cd frontend && npm run build` | exit 0 |

**Test path:** `backend/src/tests/api/test_taste_quiz_routes.py`
