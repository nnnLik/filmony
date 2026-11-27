# Plan: colon-shortcode markup

**Slug:** `colon-shortcode-markup`

Replace opaque `⟦r{id}⟧` tokens with readable `:shortcode:` emoji syntax and Discord-style `||text||` spoilers. Complete known shortcodes render as reaction images immediately; broken shortcodes stay readable text. Composer shows spoiler inner text; published view uses `SpoilerRevealBlock`. Canonicalize on write. Keep legacy parsers.

## 1. Feature artifacts and HOT

- Create `.cursor/features/colon-shortcode-markup/feature.md` with scope and acceptance criteria.
- Create `.cursor/active/colon-shortcode-markup/plan.md` and `progress.md`.
- Add `colon-shortcode-markup` as `in_progress` #1 in `.cursor/HOT.md`; keep existing in_progress items.
- Later (closeout): `result.md`, `docs/features/colon-shortcode-markup.md`, action-log fragment.

## 2. Backend shortcode migration

- Add unique `shortcode` on `ReactionType` (`backend/src/models/reaction_type.py`) plus Alembic: UNIQUE NOT NULL after backfill.
- Backfill from `asset_key`: basename without extension (`9137-gasp`), strip leading numeric prefix and hyphen (`gasp`), normalize to `[a-z0-9_+-]+` starting with a letter (so `10:30:` does not match as `:30:`). Collisions: `{stem}-{category_slug}`, then `{stem}-{id}`.
- Expose `shortcode` on `GET /api/reactions/catalog` (DAO + schema item).
- New narrow module next to `backend/src/services/cards/comment_reaction_tokens.py`: parse/canonicalize `:shortcode:` ↔ id. Do not bloat routes.
- Parser: `:([a-z][a-z0-9_+-]{0,31}):` is a reaction **only if** the shortcode exists in the catalog. Unknown `:foo:` stays literal (not 422).
- Keep `⟦r{id}⟧` and `[[r{id}]]` as legacy; unknown id still 422 on write.
- Canonicalize stored text to `:shortcode:` on write. Do not bulk-migrate old rows.
- Update seeds/fixtures (`backend/src/fixtures/reaction_type.sql`) and test stubs.

## 3. Backend spoilers (`||`)

- Extend `backend/src/services/text/spoiler_tokens.py` (`validate_spoiler_tokens`) to accept `||…||` and legacy `⟦S⟧…⟦/S⟧`.
- Rules: no nesting, inner not empty after strip; mixing both syntaxes in one text is allowed if blocks are not nested.
- Canonicalize to `||…||` on write for comments, feed posts, and watch notes.
- Mentions `⟦@slug⟧` and card refs `⟦c{id}⟧` stay unchanged.

## 4. Frontend parsers and overlay

- `frontend/src/lib/commentReactionTokens.ts`: hits for `:shortcode:`; catalog map id ↔ shortcode.
- `frontend/src/lib/spoilerTokens.ts`: `||` plus legacy `⟦S⟧…⟦/S⟧`.
- `CommentBodyWithReactionTokens.tsx`: in `annotateCharRanges`, do not hide spoiler inner text in draft/overlay; published still uses `SpoilerRevealBlock`.
- Overlay: complete known shortcode → reaction image; broken token → readable text (`:gas`); spoiler in draft → inner + `||` as visible text.
- Keep the mirror field (`CommentDraftMirrorField`) for mention-chip caret alignment. Tokens are not atomic: backspace by letter is how a shortcode is repaired.
- On edit, optionally expand legacy `⟦r12⟧` to `:gasp:` so the user sees a readable name; renderer understands both.

## 5. Frontend compose and autocomplete

- Reaction picker (`CommentReactionTokenPicker`) inserts `:shortcode:`, not `⟦r{id}⟧`.
- Colon autocomplete (same pattern as `@`): after `:` with no space, filter catalog by `shortcode`; Arrow/Enter inserts `:gasp:`.
- `frontend/src/lib/feedMentionCompose.ts`: analog of `parseActiveShortcodeQuery` / apply pick.
- `useCommentDraftEditor.ts` and `CommentDraftMirrorField.tsx`: wire insert.
- Toolbar EyeOff inserts `||spoiler||` instead of `⟦S⟧спойлер⟦/S⟧`.
- Surfaces: comments, feed post body, watch notes.

## 6. Tests and lint

- Frontend unit (vitest): shortcode parser, `10:30:` does not match, unknown `:foo:` is text, `||` spoilers, mixed legacy.
- Backend unit (`tests/unit/services/`): spoiler `||`, shortcode canonicalize, collision backfill.
- Integration: create/patch comment, feed post, and watch_note with `:gasp:` and `||x||`; legacy `⟦r⟧` / `⟦S⟧` still accepted; unknown `:foo:` not 422; unknown `⟦r{id}⟧` still 422.
- Commands (Docker-first): `make backend-lint && make backend-format && make backend-test`; `cd frontend && npm run lint && npm run test && npm run build`.

## 7. Docs, PR, and deploy

- Closeout artifacts: `result.md`, `docs/features/colon-shortcode-markup.md`, HOT + action-log.
- Branch, Conventional Commits, PR to `master` (do not push to master; Deploy lives on master).
- GitHub: **CI Frontend** (`npm run lint` + `npm run build`) and **CI Backend** (ruff + unit + integration). Vitest is not in CI — run locally.
- After green CI, merge to `master`.
- Deploy does not start itself: Actions → `Deploy` (`workflow_dispatch`) after merge when checks on `master` are green.
