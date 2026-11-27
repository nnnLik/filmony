# Colon-shortcode markup

## Scope
- Replace opaque `⟦r{id}⟧` reaction tokens with readable `:shortcode:` syntax (catalog shortcode, no spaces) in comments, feed post bodies, and watch notes.
- When a known catalog shortcode is complete, render it as the reaction image immediately (published view and composer live overlay).
- Incomplete or broken shortcodes stay readable text so the user can finish or fix them.
- Spoilers use Discord-style `||text||` in the composer as visible text; published view uses `SpoilerRevealBlock`.
- Keep parsing legacy `⟦r{id}⟧` and `⟦S⟧…⟦/S⟧`. Canonicalize on write to `:shortcode:` and `||…||`.

## Acceptance criteria
- `:shortcode:` emoji syntax uses the catalog shortcode with no spaces; a complete known shortcode renders as the reaction image immediately.
- A broken shortcode stays readable text (for example `:gas` after deleting a letter) until it is completed again.
- Spoilers use `||text||` in the composer as visible text (markers stay visible; inner text is not hidden); published output uses `SpoilerRevealBlock`.
- Legacy `⟦r{id}⟧` and `⟦S⟧…⟦/S⟧` still parse on read and in published render.
- Surfaces: comments, feed post body, and watch notes (the existing `CommentDraftMirrorField` / `CommentBodyWithReactionTokens` paths).
- On write, canonicalize reactions to `:shortcode:` and spoilers to `||…||`.
- Unknown `:foo:` stays literal text (not HTTP 422).
- Unknown `⟦r{id}⟧` still returns 422 on write.

## Out of scope
- Mentions (`⟦@slug⟧`) and card-ref (`⟦c{id}⟧`) syntax.
- Bio, watch-party chat, and share-to-Telegram HTML.
- Atomic backspace on reaction chips.
- Bulk SQL migration of existing `⟦r{id}⟧` rows to shortcode form.
