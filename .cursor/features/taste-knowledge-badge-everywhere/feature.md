# Taste Knowledge Badge Everywhere

## Goal
Show taste-quiz **accuracy %** next to other users across the app. The number means **how well the current viewer knows that user** (viewer = guesser, shown user = owner).

## Scope
- Backend: `POST /api/taste-quiz/knowledge/batch-as-guesser` — batch lookup from authenticated viewer's perspective.
- Frontend: `useTasteQuizKnowledgeOfUsers` hook; wire badge into feed, comments, film detail, subscriptions, search users, public profile.
- Fix inverted batch semantics (viewer→others, not owner→guessers).

## Acceptance Criteria
- Badge shows `accuracy_pct` only when viewer has `attempts > 0` for that owner; hidden for self.
- Single shared hook batches owner ids (max 100, deduped, sorted) via React Query.
- Surfaces: feed cards/previews, comment threads (movie card + feed post detail), `FilmDetailPage`, `SubscriptionsPage`, `SearchPage` users, `PublicProfilePage`.
- Backend pytest covers auth, empty input, max ids, omit self and zero-attempt owners.

## Out of Scope
- Profile stats Jaccard taste peers (`profile-taste-match`).
- New taste-quiz gameplay or scoring rules.
