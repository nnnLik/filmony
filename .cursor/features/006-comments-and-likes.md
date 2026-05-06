# 006 — Comments and likes

> **Статус: частично.** **Комментарии** реализованы (см. `docs/features/movie-card-comments.md` и telegram-like при необходимости). Классические **лайки** и стандартные emoji-реакции мессенджеров **не** являются целевой моделью: вместо них — **кастомные картинки-реакции** из каталога (админ задаёт ассеты, хранение в БД/URL). Актуальная спека: [`movie-card-custom-reactions/feature.md`](./movie-card-custom-reactions/feature.md) и `docs/features/movie-card-custom-reactions.md`.

## Metadata

| Field | Value |
|--------|--------|
| **Feature slug** | `comments-and-likes` |
| **Priority** | P2 |
| **Target area** | fullstack |
| **Depends on** | [001](./001-telegram-user-base.md), [005](./005-movie-rating-with-tags.md) |
| **Unlocks** | Richer engagement on cards; optional notification hooks (**009**) |

## Summary

Under each **movie card**, support **threaded comments** (or flat v1 + replies in v2), **likes on cards**, and **likes on comments**, as in [`.cursor/tech.md`](../tech.md) and “живое обсуждение” in [`.cursor/user-story.md`](../user-story.md).

## Problem

Cards need a social layer beyond ratings: discussion and lightweight reactions.

## Backend

### Responsibilities

- **Comments**: create, list (pagination, chronological or threaded), soft-delete or hard-delete policy, edit window optional.
- **Likes**: idempotent toggle or explicit like/unlike; store `(user_id, target_type, target_id)` unique.
- **Targets**: `movie_card` for card likes; `comment` for comment likes.
- **Counts**: denormalized `likes_count` / `comments_count` on card for fast lists, or compute with Redis cache — align with caching strategy in **007**.

### Data model (planned)

- **`comments`**: `id`, `card_id`, `user_id`, `parent_comment_id` nullable, `body`, `created_at`, `deleted_at` optional.
- **`likes`**: polymorphic association or separate tables per target type.

### API (planned)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/cards/{card_id}/comments` | Paginated comments |
| `POST` | `/api/cards/{card_id}/comments` | Add comment |
| `PATCH` | `/api/comments/{id}` | Edit if allowed |
| `DELETE` | `/api/comments/{id}` | Delete |
| `POST` | `/api/cards/{card_id}/like` | Toggle or like |
| `DELETE` | `/api/cards/{card_id}/like` | Unlike if not toggle |
| `POST` | `/api/comments/{id}/like` | Toggle like on comment |

### Authorization

- Only authenticated users; optional rule: only friends can comment — **product decision** (default: public comments among registered users).

### Redis

- Hot comment counts / like aggregates with TTL if needed for scale.

### Existing codebase references

| File | Note |
|------|------|
| [`backend/src/api/router.py`](../../backend/src/api/router.py) | Nested or flat routers under `/api/cards` |

### Suggested new modules

- `backend/src/api/comments/routes.py`
- `backend/src/services/comment_service.py`, `like_service.py`

## Frontend

### Responsibilities

- **Card detail** screen: comments list, composer, like button with count.
- **Comment row**: author avatar/name (link to **002**), body, like action, reply if threaded.
- Optimistic UI for likes optional; handle errors with Telegram-friendly messages.

### Existing codebase references

| File | Note |
|------|------|
| [`frontend/src/App.tsx`](../../frontend/src/App.tsx) | Shell for card route |

### Suggested new files

- `frontend/src/pages/CardDetailPage.tsx`
- `frontend/src/components/comments/CommentThread.tsx`, `CommentComposer.tsx`

## Acceptance criteria

- [ ] User can add comment on a visible card; list updates or refetches correctly.
- [ ] Card like toggles idempotently; counts consistent after refresh.
- [ ] Comment likes work independently from card likes.
- [ ] Pagination works for long threads; no duplicated rows on retry.

## Out of scope

- Rich text/markdown (plain text v1).
- Report/abuse workflow.

## References

- [`.cursor/user-story.md`](../user-story.md) — шаг 4, оценки друзей рядом (карточка как hub).
- [005](./005-movie-rating-with-tags.md)
