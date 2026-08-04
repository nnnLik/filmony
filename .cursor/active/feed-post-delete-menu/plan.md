# Feed post delete + owner overflow menu — plan

**Feature slug:** `feed-post-delete-menu`  
**Status:** in_progress

---

## 1. Backend — delete service

### 1.1 Create `DeleteFeedPostService`
**File:** `backend/src/services/feed_posts/delete_feed_post.py`

Mirror `DeleteFeedPostCommentService` (`backend/src/services/feed_posts/delete_feed_post_comment.py`):

- `@dataclass` with `_session: AsyncSession`
- `@classmethod build(cls, session) -> Self`
- `async def execute(self, feed_post_id: int, actor_user_id: UUID) -> None`
- Module-level typed errors (or nested on service per repo convention):
  - `FeedPostNotFoundError` — no row for `feed_post_id`
  - `FeedPostForbiddenError` — `post.user_id != actor_user_id`
- Load post by id; raise not found / forbidden; `session.delete(post)` + `commit`
- Docstring: hard delete; comments cascade via `feed_post_comment.feed_post_id` FK `ON DELETE CASCADE`

### 1.2 Export service
- Add to `backend/src/services/feed_posts/__init__.py` if package re-exports services (match siblings).

---

## 2. Backend — API route

### 2.1 Add DELETE handler
**File:** `backend/src/api/feed_posts/routes.py`

```text
DELETE /api/feed-posts/{post_id}
Status: 204
Summary: Удалить пост ленты
```

- Auth: `CurrentUser` required
- Call `DeleteFeedPostService.build(db).execute(post_id, user.id)`
- Map errors:
  - `FeedPostNotFoundError` → 404 `feed post not found`
  - `FeedPostForbiddenError` → 403 `forbidden`
- Return `Response(status_code=204)`
- Place near existing `PATCH /{post_id}` (update) for discoverability

---

## 3. Backend — tests

### 3.1 Service + route tests
**File:** `backend/src/tests/services/feed_posts/test_feed_post_delete.py` (or extend existing feed post test module if one exists)

Cases:
1. **Happy path:** author creates post + comment → DELETE → 204; post and comments absent on subsequent GET/list queries
2. **403:** other user attempts delete
3. **404:** unknown `post_id`
4. **401:** unauthenticated (if pattern exists in sibling tests)

Run: `make backend-test-one target=src/tests/services/feed_posts/test_feed_post_delete.py` (adjust path after creation)

---

## 4. Frontend — API client

### 4.1 `deleteFeedPost`
**File:** `frontend/src/api/feedPostApi.ts`

- `export async function deleteFeedPost(postId: number): Promise<void>`
- `DELETE /api/feed-posts/${postId}` via `apiFetch`; expect 204; throw `ApiError` on failure
- Mirror `deleteFeedPostComment` error handling

---

## 5. Frontend — overflow menu component

### 5.1 Post owner actions
**Approach:** Reuse `CommentHeaderActions` pattern or add thin `PostHeaderActions`.

**Preferred:** `frontend/src/components/feed/PostHeaderActions.tsx`

- Props: `canManage`, `onEdit`, `onDelete`, `deleteBusy`, `disabled`
- Labels (Russian, match comments): **Изменить**, **Удалить**, **Удаление…**
- ⋯ `IconButton` + popover menu — copy styling from `CommentHeaderActions` (`ICON_BUTTON_CLASS`, `MENU_POP_CLASS`, etc.)
- No Reply / Share / PublishToFeed unless post header already needs them later

**Alternative:** Extend `CommentHeaderActions` with optional `hideReply` — only if duplication is excessive; prefer separate thin component for post header.

---

## 6. Frontend — `FeedPostCard`

**File:** `frontend/src/components/feed/FeedPostCard.tsx`

1. Remove inline «Редактировать» text button (lines ~851–865 area).
2. When `isOwn && !editingPost`, render `PostHeaderActions` in header row (right side or after timestamp — align with comment layout on detail).
3. **Изменить** → existing `setEditingPost(true)` flow (preserve `editBody`, `editError` reset).
4. **Удалить** → confirm then API:
   - Confirm string (Russian): `Удалить пост? Все комментарии к нему тоже будут удалены.`
   - Call `deleteFeedPost(post.id)`
   - On success: invoke new optional prop `onPostDeleted?: (postId: number) => void` so parent removes card from list
5. Track `deleteBusy` state; disable menu while pending
6. Stop propagation on menu interactions when `linkToDetail` (same as edit button today)

---

## 7. Frontend — `FeedPostDetailPage`

**File:** `frontend/src/pages/FeedPostDetailPage.tsx`

1. Wire delete on the embedded `FeedPostCard` via `onPostDeleted` or page-level handler passed into card
2. After successful delete: `navigate(-1)` or `navigate('/feed')` (prefer back if history exists, else feed — match app patterns)
3. Ensure comment delete confirm strings stay unchanged

---

## 8. Frontend — feed list cache / state

**Files:** `frontend/src/pages/FeedPage.tsx`, `frontend/src/pages/ProfilePage.tsx`, `frontend/src/pages/PublicProfilePage.tsx`

- Pass `onPostDeleted` to `FeedPostCard` where viewer owns post:
  - Remove post from local list state / react-query cache invalidation
  - Pattern: filter out deleted `post.id` from items array or invalidate feed query key if used
- Minimal change: callback prop on card; parents that render lists handle removal

---

## 9. Verification

- Docker: `make backend-test-one target=…delete…`
- Frontend: `cd frontend && npm run lint && npm run build`
- Manual: own post in feed → ⋯ → delete → confirm → card gone; detail → delete → navigates away; non-owner sees no ⋯

---

## 10. Docs closeout (after implementation)

- `.cursor/active/feed-post-delete-menu/result.md`
- `docs/features/feed-post-delete-menu.md`
- Action-log fragment + HOT `recent_completed` update

---

## File checklist

| Area | File | Action |
|------|------|--------|
| Backend | `services/feed_posts/delete_feed_post.py` | create |
| Backend | `api/feed_posts/routes.py` | add DELETE |
| Backend | `tests/.../test_feed_post_delete.py` | create |
| Frontend | `api/feedPostApi.ts` | add `deleteFeedPost` |
| Frontend | `components/feed/PostHeaderActions.tsx` | create |
| Frontend | `components/feed/FeedPostCard.tsx` | menu + remove edit link |
| Frontend | `pages/FeedPostDetailPage.tsx` | navigate on delete |
| Frontend | `pages/FeedPage.tsx` (+ profile pages) | `onPostDeleted` wiring |
