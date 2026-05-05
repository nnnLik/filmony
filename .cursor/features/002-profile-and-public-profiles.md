# 002 — Profile and viewing others’ profiles

## Metadata

| Field | Value |
|--------|--------|
| **Feature slug** | `profile-and-public-profiles` |
| **Priority** | P1 |
| **Target area** | fullstack |
| **Depends on** | [001 — Telegram user](./001-telegram-user-base.md) |
| **Unlocks** | Manual discovery of taste (“ручной поиск совпадений”) per [user-story](../user-story.md) |

## Summary

Let each user maintain a **visible profile** (display name, avatar, optional bio/stats) and browse **other users’ profiles** with their **movie cards** (reviews/ratings list). This matches the product goal: “чужие профили с их карточками для ручного поиска совпадений” ([`.cursor/tech.md`](../tech.md)).

## Problem

After authentication, users need identity beyond Telegram defaults: discoverability among friends and strangers, and a **place to see what someone else watched and how they rated it**—without relying only on the feed or recommendations.

## Backend

### Responsibilities

- **Own profile**: read/update fields allowed by product (e.g. display name override, bio, visibility flags if needed later).
- **Public profile**: by **internal user id** or **public slug** (choose one in implementation; slug is nicer for sharing).
- **Profile summary**: optional aggregates — count of cards, friends count (when **003** exists), last activity — keep lightweight for v1.
- **Privacy**: define what is visible to non-friends (minimum: public cards list per product; tighten later if needed).

### Data model (planned)

- Extend **`users`** or separate **`user_profiles`**: `display_name`, `bio`, `avatar_url` (or Telegram photo cache reference).
- **`movie_cards`** / ratings table will be referenced from **005**; profile endpoints list **that user’s cards** with pagination.

### API (planned)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/me/profile` | Full editable profile for current user |
| `PATCH` | `/api/me/profile` | Update allowed fields |
| `GET` | `/api/users/{user_id}` or `/api/users/by-slug/{slug}` | Public profile + pagination cursor for cards |
| `GET` | `/api/users/{user_id}/cards` | Paginated list of their movie cards (if split from single resource) |

### Caching (Redis)

- Optional short TTL cache for public profile + first page of cards ([`.cursor/tech.md`](../tech.md) — typical feed/card caching patterns).

### Existing codebase references

| File | Note |
|------|------|
| [`backend/src/api/router.py`](../../backend/src/api/router.py) | Mount profile routers under `/api` |
| [`backend/src/conf/settings.py`](../../backend/src/conf/settings.py) | Any limits (page size defaults) |

### Suggested new modules

- `backend/src/api/profile/` — `me` + `users` routes.
- `backend/src/schemas/profile.py` — Pydantic models.
- `backend/src/services/profile_service.py` — orchestration.

## Frontend

### Responsibilities

- **“Мой профиль”** screen: edit fields supported by API; show Telegram-linked identity from **001**.
- **Чужой профиль**: route `/u/:id` or `/u/:slug`; header with name/avatar; **tabs or list** of their movie cards (cards UI shared with **005**/**007**).
- Navigation entry from future surfaces: friend list (**003**), film top raters, comments (**006**).
- Use **@telegram-apps/telegram-ui** components per project standards (see [`.cursor/rules/frontend-react-telegram-ui-standards.mdc`](../rules/frontend-react-telegram-ui-standards.mdc)).

### Existing codebase references

| File | Note |
|------|------|
| [`frontend/src/App.tsx`](../../frontend/src/App.tsx) | Will need router (e.g. React Router) when multiple screens exist |
| [`frontend/vite.config.ts`](../../frontend/vite.config.ts) | SPA fallback for deep links to `/u/...` if required by hosting |

### Suggested new files

- `frontend/src/pages/ProfilePage.tsx`, `PublicProfilePage.tsx`
- `frontend/src/components/profile/ProfileHeader.tsx`
- `frontend/src/routes.tsx` — route definitions

## Acceptance criteria

- [ ] Authenticated user can open own profile and persist allowed edits; validation errors are shown inline.
- [ ] Any authenticated user can open another user’s public profile by stable identifier and see a paginated list of their **movie cards** (once cards exist; until then stub empty list with correct contract).
- [ ] Unauthorized access to private resources returns 404 or 403 per chosen privacy model (document in API).
- [ ] Profile loads within acceptable time; list supports infinite scroll or “load more”.

## Out of scope

- Blocking users, follower counts, or non-friend full privacy matrix (unless product adds later).
- Inline editing of someone else’s content.

## References

- [`.cursor/user-story.md`](../user-story.md) — “Способ 3. Ручной поиск”, профили и фильтры.
- [001 — Telegram user](./001-telegram-user-base.md)
