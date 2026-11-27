# Colon-shortcode markup

Readable `:shortcode:` reaction tokens and Discord-style `||spoiler||` blocks in comments, feed post bodies, and watch notes. Complete catalog shortcodes render as reaction images immediately; incomplete or unknown names stay as plain text. On write, the backend canonicalizes reactions to `:shortcode:` and spoilers to `||…||`. Legacy `⟦r{id}⟧` / `⟦S⟧…⟦/S⟧` still parse on read.

## `:shortcode:` syntax

- Form: `:shortcode:` using the catalog shortcode (no spaces). Pattern: `:([a-z][a-z0-9_+-]{0,31}):`.
- A complete **known** shortcode is a reaction: published view and composer overlay show the catalog image.
- Incomplete or broken tokens stay readable text so the user can finish or fix them (for example `:gas` after deleting a letter).
- Unknown `:foo:` stays literal text. It is **not** a validation error (HTTP 200 on write).
- `10:30` and similar clock-like colons are not treated as a shortcode query (the character before `:` is alphanumeric).

Example stored text:

```
вау :gasp: класс
```

## Spoilers (`||text||`)

Text is stored as a plain string with inline markers (same family as reactions and `@mention`):

```
||скрытый текст||
```

- Backend checks balance, forbids nesting, and rejects empty inner text after strip.
- Mixing `||…||` and legacy `⟦S⟧…⟦/S⟧` in one string is allowed if blocks are not nested.
- Published view uses `SpoilerRevealBlock` (hidden until tap).
- Composer / draft overlay shows markers and inner text as visible characters — spoilers are not hidden while editing.

## Edit vs published

| Surface | Composer / draft overlay (`annotateCharRanges`) | Published render |
| --- | --- | --- |
| Known `:shortcode:` | Reaction image immediately | Reaction image |
| Incomplete / unknown `:name:` | Readable text | Readable text |
| `||inner||` | `||` markers + inner text visible | `SpoilerRevealBlock` |
| Legacy `⟦r{id}⟧` / `⟦S⟧…⟦/S⟧` | Parsed; on **enter edit**, known reaction ids expand to `:shortcode:` | Same parsers; spoilers hidden |

Tokens are not atomic: backspace deletes by letter so a shortcode can be repaired. Entering comment or feed-post body edit loads the catalog and expands `⟦r{id}⟧` / `[[r{id}]]` to `:shortcode:` when the id is known; catalog load failure leaves legacy markers.

## Legacy `⟦r⟧` / `⟦S⟧`

- Read and published render still accept `⟦r{id}⟧`, ASCII `[[r{id}]]`, and `⟦S⟧…⟦/S⟧`.
- Unknown legacy reaction **id** still fails write validation.
- Comments: unknown `⟦r{id}⟧` → **422**.
- Feed post body: unknown `⟦r{id}⟧` → **400** (`FeedPostBodyValidationError`, not 422).
- Existing rows are not bulk-migrated. Canonical form is written on the next create/update.

## Catalog `shortcode` field

- `ReactionType.shortcode` is unique, not null, derived from `asset_key` (basename without extension, strip leading `digits-`, keep `[a-z0-9_+-]`, must start with a letter). Collisions: `{stem}-{category_slug}`, then `{stem}-{id}`.
- `GET /api/reactions/catalog` exposes `shortcode` on each item (`ReactionCatalogItem` / `ReactionCatalogItemResponse`).
- Frontend picker insert uses `reactionTokenForInsert(id, shortcode)` → `:shortcode:` when the name is present.

## Canonicalize on write

When the body contains `:`, `⟦r`, or `[[r`, validators load id→shortcode maps and call `rewrite_reaction_tokens`:

- Known `:name:` stays `:name:`.
- Unknown `:foo:` stays literal.
- Known `⟦r{id}⟧` / `[[r{id}]]` become `:shortcode:`.
- Unknown legacy id raises; max length is re-checked after rewrite.
- `validate_spoiler_tokens` then rewrites every valid spoiler block to `||inner||`.
- Mentions `⟦@slug⟧` and card-refs `⟦c{id}⟧` are unchanged.

Applies to comments, feed post bodies, and watch notes (card create/update, planned cards, watchlist create/update).

## Surfaces

- Card and feed-post **comments** (`CommentComposeBar`, `CommentThreadSection`, `CommentListItem`, `EngagementCommentsRow`, feed inline drafts).
- **Feed post body** (`FeedComposeSheet` compose, `FeedPostCard` body edit).
- **Watch notes** (`CardFormFields`; backend card and watchlist services).

Shared UI path: `CommentDraftMirrorField` + `CommentBodyWithReactionTokens`.

## Autocomplete

After a standalone `:` with no space (Discord-like), `parseActiveShortcodeQuery` opens a catalog filter:

- Prefix matches first, then substring; cap 24.
- Arrow / Enter insert `:shortcode:` (`useReactionShortcodePicker` + `ReactionShortcodeSuggestPortal`).
- Closing an already complete `:gasp:` does not reopen the picker; `10:30` / `hello:` are rejected.
- Mention picker wins keydown when both are open.
- Toolbar EyeOff inserts `||спойлер||` (placeholder) instead of `⟦S⟧спойлер⟦/S⟧`.

## Out of scope

- Mentions (`⟦@slug⟧`) and card-ref (`⟦c{id}⟧`) syntax.
- Bio, watch-party chat, and share-to-Telegram HTML.
- Atomic backspace on reaction chips.
- Bulk SQL migration of existing `⟦r{id}⟧` rows to shortcode form.

## Technical files

- `backend/src/services/text/reaction_shortcodes.py`
- `backend/src/services/text/spoiler_tokens.py`
- `backend/src/services/cards/comment_reaction_tokens.py`
- `backend/src/services/feed_posts/validate_feed_post_body.py`
- `backend/src/models/reaction_type.py`
- `frontend/src/lib/commentReactionTokens.ts`
- `frontend/src/lib/commentShortcodeCompose.ts`
- `frontend/src/lib/spoilerTokens.ts`
- `frontend/src/hooks/useReactionShortcodePicker.ts`
- `frontend/src/components/comments/ReactionShortcodeSuggestPortal.tsx`
- `frontend/src/components/comments/CommentBodyWithReactionTokens.tsx`

## Verification

```bash
cd frontend && npm run lint && npm run test && npm run build
make backend-lint && make backend-format && make backend-test
```

Host-venv evidence in this cloud agent (Docker unavailable): frontend `npm test` 156 passed, `npm run lint` and `npx tsc -b` passed; backend ruff plus unit pytest for shortcode/spoiler/validators passed. Integration HTTP tests and `vite build` were not completed here (`vite` failed on Cloudflare `registerHooks` in this image). After merge to `master`, production deploy is Actions → **Deploy** (`workflow_dispatch`); it does not start itself.
