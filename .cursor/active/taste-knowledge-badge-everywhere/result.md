# Taste Knowledge Badge Everywhere — Result

Status: complete

## Implemented

- **Product meaning:** % next to a user = **how well YOU know THEM** (viewer as guesser, that user as owner).
- **Backend:** `POST /api/taste-quiz/knowledge/batch-as-guesser` + `BatchTasteQuizKnowledgeAsGuesserService`.
- **Frontend:** `useTasteQuizKnowledgeOfUsers`; badge on feed, comments, film detail, subscriptions, search users, public profile.
- **Semantics fix:** batch endpoint and hook use viewer→owner direction (not inverted).

## Changed Files

**Backend**
- `backend/src/services/taste_quiz/batch_knowledge_as_guesser.py` (new)
- `backend/src/services/taste_quiz/__init__.py`
- `backend/src/api/taste_quiz/routes.py`
- `backend/src/api/taste_quiz/schemas.py`
- `backend/src/tests/api/test_taste_quiz_routes.py`

**Frontend**
- `frontend/src/hooks/useTasteQuizKnowledgeOfUsers.ts` (new)
- `frontend/src/api/tasteQuizApi.ts`
- `frontend/src/api/tasteQuizTypes.ts`
- `frontend/src/lib/tasteQuizQueryKeys.ts`
- `frontend/src/components/tasteQuiz/TasteQuizCommentAuthorBadge.tsx`
- `frontend/src/components/feed/FeedCard.tsx`
- `frontend/src/components/feed/FeedPostCard.tsx`
- `frontend/src/pages/FeedPostDetailPage.tsx`
- `frontend/src/pages/MovieCardDetailPage.tsx`
- `frontend/src/pages/FilmDetailPage.tsx`
- `frontend/src/pages/SubscriptionsPage.tsx`
- `frontend/src/pages/SearchPage.tsx`
- `frontend/src/pages/PublicProfilePage.tsx`

## Verification

| Check | Command | Result |
|-------|---------|--------|
| Backend pytest | `make backend-test-one target=src/tests/api/test_taste_quiz_routes.py::test_knowledge_batch_as_guesser_omits_zero_attempts_and_self` | passed |
| Frontend lint | `cd frontend && npm run lint` | exit 0 |
| Frontend build | `cd frontend && npm run build` | exit 0 |

**Paths:** `backend/src/tests/api/test_taste_quiz_routes.py`; touched frontend under `frontend/src/hooks/`, `frontend/src/api/`, `frontend/src/lib/`, `frontend/src/components/tasteQuiz/`, `frontend/src/components/feed/`, `frontend/src/pages/`.

## Limitations

- Max 100 owner ids per batch request.
- Badge only when viewer has played taste quiz against that owner (`attempts > 0`).
