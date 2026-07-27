# Taste Knowledge Badge Everywhere — Progress

Status: complete

## Log

- Backend: `BatchTasteQuizKnowledgeAsGuesserService`, route, schemas, pytest — done.
- Frontend: hook, API client, query keys; inverted semantics fixed — done.
- Wired: `FeedCard`, `FeedPostCard`, `FeedPostDetailPage`, `MovieCardDetailPage`, `FilmDetailPage`, `SubscriptionsPage`, `SearchPage`, `PublicProfilePage` — done.
- Feature delivery artifacts and action log — done.

## Verification

- Backend: `make backend-test-one target=src/tests/api/test_taste_quiz_routes.py::test_knowledge_batch_as_guesser_omits_zero_attempts_and_self` — passed.
- Frontend: `cd frontend && npm run lint && npm run build` — exit 0 (2026-07-27).
