# Taste Knowledge Badge Everywhere — Plan

Status: complete

## Steps

1. **Backend service** — `BatchTasteQuizKnowledgeAsGuesserService`: guesser → many owners, omit self and zero-attempt pairs.
2. **API route** — `POST /api/taste-quiz/knowledge/batch-as-guesser`; request `owner_user_ids`, response `items` map.
3. **Tests** — auth, empty, 422 over limit, happy path with self/stranger/zero-attempt omitted.
4. **Frontend API + hook** — `batchTasteQuizKnowledgeAsGuesser`, `useTasteQuizKnowledgeOfUsers` → `knowledgeByOwnerId`.
5. **Badge wiring** — `TasteQuizCommentAuthorBadge` + user list surfaces (feed, comments, film, subscriptions, search, public profile).
6. **Docs** — feature lifecycle artifacts and `docs/features/taste-knowledge-badge-everywhere.md`.
