---
name: product-release-feed-post
description: >-
  Drafts and publishes a user-facing Russian feed post (пост в ленте / FeedPost)
  after a production deploy. Use when the user asks to announce updates, changelog,
  пост в приложении, пост в ленте, or after listing shipped user-facing features;
  also offer proactively right after a successful prod ship.
---

# Product release feed post

Operational skill for **пост в ленте** announcements on prod. Invariants: [`.cursor/rules/product-release-feed-post.mdc`](../../rules/product-release-feed-post.mdc). Voice, forbidden terms, canonical example, and prod publish snippet: [reference.md](reference.md).

## When to use

- **After production deploy** or successful prod ship — offer a feed post (do not auto-publish)
- User asks to **announce updates**, **changelog**, **пост в приложении**, or **пост в ленте**
- User just reviewed **shipped user-facing features** (last day, since last deploy, HOT `recent_completed`)
- **Do not offer** when the ship is infra-only (healthcheck, CI, docs-only, no user-visible change)

## Offer-first (mandatory)

1. After deploy or feature recap, **always** ask: «Опубликовать пост в ленте об обновлениях?»
2. **If you already have the user-facing change list** (e.g. you just listed shipped features), include the **full draft** in that same message — do not wait for yes before drafting.
3. **If you do not yet have the list**, wait for explicit yes, then gather and draft (Steps 1–2).
4. **Publish only** after the user confirms the draft text **and** `profile_slug` (default `u83128ffb7116` / makhm_ra). **Never auto-publish.**
5. If the user declines, stop — do not publish.

## Steps

### 1. Gather sources

Skip when the user-facing change list is already in context from a deploy or feature recap (draft was included in the offer). Otherwise run after the user agrees.

Collect only **user-facing** changes that are **already on prod**:

| Source | What to extract |
|--------|-----------------|
| Git since last deploy / last day | `feat` / `fix` with product impact — not uncommitted work |
| `.cursor/HOT.md` | `recent_completed` slugs → first paragraph of `docs/features/{slug}.md` |
| Feature docs | `docs/features/*.md` — what the user sees, not implementation |

**Exclude:** uncommitted or in-progress work, infra/CI/healthcheck, docs-only edits, internal refactors with no UI change. If nothing user-facing shipped, say so — do not offer a post.

### 2. Draft the post

Follow [reference.md](reference.md):

- Russian, founder/product voice, grouped by product area (Профиль / Фильмы / Просмотр / …)
- Short bullets with `•`; warm close (e.g. «Приятных просмотров 🎬»)
- **No** commits, PRs, slugs, API names, file paths, or engineering jargon

Present the **complete draft** to the user (unless already shown in the offer message). Revise until they approve text **and** `profile_slug`.

### 3. Publish on prod (API only)

**Prod path:** SSH `homelab` → `docker exec -i -w /opt/app filmony-backend python -` (see [reference.md](reference.md) for the full snippet).

- Resolve `User.profile_slug` → internal id → `IssueSessionJwtService`
- `POST http://127.0.0.1:${PORT}/api/feed-posts` with JSON `{body, image_url: null, referenced_movie_card_id: null, source_comment_id: null}`
- **`PORT` from container env** — never hardcode `8000`
- **Never print the JWT** or paste secrets into chat
- **Never use raw SQL** for normal publish (skips follower Telegram notify + SSE bump)
- Local Docker is **not** prod

### 4. Report back

Tell the user:

- Feed post **`id`** (and `created_at` if useful)
- Post is visible in **global feed** and author **profile**
- Do not dump JWT, `DATABASE_URL`, or full user UUID unless debugging and user asked

## Safety

- Confirm **text and account** with the user before every publish
- Default announcement account: `u83128ffb7116` (makhm_ra) — confirm if different
- SQL insert is **fallback-not-allowed** unless API is down **and** user explicitly accepts missing notifications (see reference.md)
- Do not announce uncommitted work or infra-only changes

## Additional resources

- [reference.md](reference.md) — writing rules, forbidden terms, canonical example, prod API snippet
- [`.cursor/rules/product-release-feed-post.mdc`](../../rules/product-release-feed-post.mdc) — rule invariants
