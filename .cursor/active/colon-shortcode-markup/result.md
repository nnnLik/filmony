# Result — colon-shortcode-markup

Status: **in_progress** (implementation + tests complete 2026-08-24T164500Z; GitHub PR creation blocked from this agent)

## Implemented

- Catalog reactions use readable `:shortcode:` (no spaces). Known complete tokens render as the reaction image in published view and in the composer overlay; incomplete or unknown names stay readable text.
- Spoilers use Discord-style `||text||`. Draft overlay keeps markers and inner text visible; published view uses `SpoilerRevealBlock`. Nested mixed spoiler syntax is rejected.
- Legacy `⟦r{id}⟧` / `[[r{id}]]` and `⟦S⟧…⟦/S⟧` still parse on read. Write path canonicalizes reactions to `:shortcode:` and spoilers to `||…||`.
- `GET /api/reactions/catalog` exposes `shortcode`. Picker insert, colon autocomplete, and edit-mode expand of legacy reaction ids use that field.
- Surfaces: comments, feed post bodies, and watch notes (shared `CommentDraftMirrorField` / `CommentBodyWithReactionTokens` paths).
- Unknown `:foo:` stays literal (not 422). Unknown legacy `⟦r{id}⟧` still fails write: comments **422**, feed post body **400**.

## Changed files

### Backend — model, migration, catalog

- `backend/src/models/reaction_type.py`
- `backend/src/migrations/versions/k1l2m3n4o567_reaction_type_shortcode.py`
- `backend/src/api/reactions/schemas.py`
- `backend/src/api/reactions/routes.py`
- `backend/src/services/reactions/list_reaction_catalog.py`
- `fixtures/reaction_type.sql`
- `scripts/upload_reactions_to_rustfs.py`

### Backend — rewrite and write canonicalize

- `backend/src/services/text/reaction_shortcodes.py`
- `backend/src/services/text/spoiler_tokens.py`
- `backend/src/services/cards/comment_reaction_tokens.py`
- `backend/src/services/feed_posts/validate_feed_post_body.py`
- `backend/src/services/cards/create_user_card.py`
- `backend/src/services/cards/create_planned_user_card.py`
- `backend/src/services/cards/update_user_card.py`
- `backend/src/services/watchlist/create_watchlist_entry.py`
- `backend/src/services/watchlist/update_watchlist_entry.py`

### Backend — tests

- `backend/src/tests/unit/services/test_reaction_shortcodes.py`
- `backend/src/tests/unit/services/test_spoiler_tokens.py`
- `backend/src/tests/unit/services/cards/test_comment_reaction_tokens.py`
- `backend/src/tests/unit/services/feed_posts/test_validate_feed_post_body.py`
- `backend/src/tests/unit/api/reactions/test_catalog_schema.py`
- `backend/src/tests/integration/api/test_reactions_routes.py`
- `backend/src/tests/integration/api/test_cards_routes.py`
- `backend/src/tests/integration/api/test_feed_posts_routes.py`

### Frontend — parsers, picker, overlay

- `frontend/src/api/profileTypes.ts`
- `frontend/src/lib/commentReactionTokens.ts`
- `frontend/src/lib/commentShortcodeCompose.ts`
- `frontend/src/lib/spoilerTokens.ts`
- `frontend/src/lib/__tests__/commentReactionTokens.test.ts`
- `frontend/src/lib/__tests__/commentShortcodeCompose.test.ts`
- `frontend/src/lib/__tests__/spoilerTokens.test.ts`
- `frontend/src/hooks/useReactionShortcodePicker.ts`
- `frontend/src/hooks/useCommentDraftEditor.ts`
- `frontend/src/components/comments/ReactionShortcodeSuggestPortal.tsx`
- `frontend/src/components/comments/CommentBodyWithReactionTokens.tsx`
- `frontend/src/components/comments/CommentReactionTokenPicker.tsx`

### Frontend — surfaces

- `frontend/src/components/comments/CommentComposeBar.tsx`
- `frontend/src/components/comments/CommentThreadSection.tsx`
- `frontend/src/components/comments/CommentListItem.tsx`
- `frontend/src/components/create/CardFormFields.tsx`
- `frontend/src/components/feed/EngagementCommentsRow.tsx`
- `frontend/src/components/feed/FeedCard.tsx`
- `frontend/src/components/feed/FeedComposeSheet.tsx`
- `frontend/src/components/feed/FeedPostCard.tsx`
- `frontend/src/components/reactions/reactionStrip/ReactionStripPopover.tsx`
- `frontend/src/pages/MovieCardDetailPage.tsx`
- `frontend/src/pages/FeedPostDetailPage.tsx`

### Docs / memory (this closeout)

- `docs/features/colon-shortcode-markup.md`
- `.cursor/active/colon-shortcode-markup/progress.md`
- `.cursor/memory/logs/2026-08-24T163000Z-colon-shortcode-markup-docs.md`
- `.cursor/memory/logs/2026-08-24T164500Z-colon-shortcode-markup-test.md`

## Verification

Commands and results recorded 2026-08-24T164500Z:

```bash
ruff check
ruff format --check
# pytest unit (full suite, before nested spoiler tests)
# pytest unit: backend/src/tests/unit/services/test_spoiler_tokens.py (after nested fix)
# targeted pytest integration (catalog / comments / feed-post rewrite)
cd frontend && npm run lint
cd frontend && npm test
cd frontend && npx tsc -b
cd frontend && npm run build
```

| Command | Result |
|---|---|
| `ruff check` + `ruff format --check` | pass |
| pytest unit (full suite) | **239 passed** (before nested spoiler tests) |
| `backend/src/tests/unit/services/test_spoiler_tokens.py` after nested-spoiler fix | **13 passed** (2 nested tests added; do not treat 239+2 as a re-run of the full unit suite) |
| targeted integration (catalog / comments / feed-post rewrite) | **20 passed** |
| `cd frontend && npm run lint` | **0 errors**; 1 preexisting `WatchParty` warning (untouched) |
| `cd frontend && npm test` (vitest) | **156 passed** |
| `cd frontend && npx tsc -b` | pass |
| `cd frontend && npm run build` | **failed locally** on Node 22 Cloudflare plugin (`registerHooks`); CI Frontend uses Node 24 |

## PR / deploy

- Branch `ai/colon-shortcode-markup-ec87` is on GitHub: `git ls-remote origin refs/heads/ai/colon-shortcode-markup-ec87` → `085b7d2`.
- Compare: https://github.com/nnnLik/filmony/compare/master...ai/colon-shortcode-markup-ec87
- Origin inbound GitHub mirror cannot create Origin PRs; `gh` is not authenticated. GitHub PR creation is blocked from this agent.
- Production **Deploy** stays GitHub Actions `workflow_dispatch` after merge to `master`; merge does not start a deploy.

## Limitations

- Full Docker `make backend-test` (unit + integration sequentially) was not re-run as one command; unit 239 and targeted integration 20 were recorded separately, then two nested spoiler unit tests were added (`test_spoiler_tokens` 13 passed after that fix).
- Local `npm run build` failed on Node 22 Cloudflare plugin; rely on CI Frontend (Node 24) after a GitHub PR exists.
- Unknown feed-post legacy reaction token is **400**, not 422 (`FeedPostBodyValidationError`). Comments still return **422** for the same unknown `⟦r{id}⟧`. Unknown `:foo:` is accepted as literal text on both surfaces.
- Mentions, card-refs, bio, watch-party chat, share-to-Telegram HTML, atomic chip backspace, and bulk SQL rewrite of old `⟦r{id}⟧` rows are out of scope.

## Next steps

- Open a GitHub PR from `ai/colon-shortcode-markup-ec87` to `master` (blocked here: Origin inbound mirror + unauthenticated `gh`). Use the compare URL above.
- After green **CI Frontend** and **CI Backend**, merge; then Actions → Deploy when checks on `master` are green.
