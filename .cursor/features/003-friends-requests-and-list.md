# 003 — Friends (requests and list)

## Metadata

| Field | Value |
|--------|--------|
| **Feature slug** | `friends-requests-and-list` |
| **Priority** | P1 |
| **Target area** | fullstack |
| **Depends on** | [001](./001-telegram-user-base.md) |
| **Unlocks** | Co-view invitations (user-story), friend-weighted feed (**007**), friend ratings on cards |

## Summary

Implement the **social graph** for “друзья”: send and accept/decline **friend requests**, maintain an **asymmetric or symmetric friendship** model (product default: mutual friendship after accept), and expose **lists** for picker UIs (invite friends to rate, “кинуть другу”, etc.) as described in [`.cursor/tech.md`](../tech.md) and [`.cursor/user-story.md`](../user-story.md).

## Problem

The product relies on **friends** for feeds, side-by-side ratings on a film card, and invitations. Without persisted friendships and request workflow, those flows cannot be implemented.

## Backend

### Responsibilities

- **Request lifecycle**: `pending` → `accepted` | `declined` | `cancelled`.
- Prevent duplicates and self-requests; handle idempotent “accept” safely.
- **Queries**: incoming requests, outgoing requests, accepted friends list with optional search by username/display name.
- **Notifications**: push events to **009** (Telegram) on new request / acceptance — async via Celery when configured.

### Data model (planned)

- Table **`friendships`** or **`friend_requests`**: `from_user_id`, `to_user_id`, `status`, `created_at`, `updated_at`, unique constraint on the pair for pending/active logic (exact schema depends on symmetric vs directed model).

### API (planned)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/friends/requests` | Body: `to_user_id` — send request |
| `POST` | `/api/friends/requests/{id}/accept` | Accept |
| `POST` | `/api/friends/requests/{id}/decline` | Decline |
| `DELETE` | `/api/friends/requests/{id}` | Cancel outgoing |
| `GET` | `/api/friends` | Accepted friends (paginated, searchable) |
| `GET` | `/api/friends/requests/incoming` | Pending incoming |
| `GET` | `/api/friends/requests/outgoing` | Pending outgoing |

### Authorization

- All endpoints require auth (**001**); verify actor owns the request or is the recipient.

### Redis

- Optional cache of friend ids for quick “is_friend” checks on other endpoints (invalidate on accept/remove).

### Existing codebase references

| File | Note |
|------|------|
| [`backend/src/api/router.py`](../../backend/src/api/router.py) | Include friends router |

### Suggested new modules

- `backend/src/api/friends/routes.py`
- `backend/src/services/friendship_service.py`
- `backend/src/models/friendship.py`

## Frontend

### Responsibilities

- **Friends hub**: tabs — Friends | Incoming | Outgoing | Search/add by username or internal id (product decision).
- **Actions**: Accept / Decline / Cancel with Telegram UI patterns (haptics optional via SDK).
- **Entry points**: link from profile (**002**); share deep link for “add me” if product wants (optional).
- Reuse list patterns for **invite picker** when implementing co-view / share movie flows from user-story.

### Existing codebase references

| File | Note |
|------|------|
| [`frontend/src/App.tsx`](../../frontend/src/App.tsx) | Navigation shell will grow with router |

### Suggested new files

- `frontend/src/pages/FriendsPage.tsx`
- `frontend/src/components/friends/FriendList.tsx`, `RequestRow.tsx`
- `frontend/src/api/friends.ts`

## Acceptance criteria

- [ ] User A can send a request to B; B sees it in incoming; A sees it in outgoing.
- [ ] B accepts → both appear in each other’s friends list; duplicate accept is handled safely.
- [ ] Decline/cancel moves request to terminal state; no duplicate friendship rows.
- [ ] Friends list is usable as data source for multi-select (invite flows in later features).
- [ ] API returns consistent error codes for blocked cases (self-request, duplicate pending).

## Out of scope

- Group chats, friend suggestions algorithm (could tie to **008** later).
- Removing friends (add small section if product requires — easy DELETE `/api/friends/{user_id}`).

## References

- [`.cursor/user-story.md`](../user-story.md) — “Зови друзей дооценить”, лента друзей.
- [001](./001-telegram-user-base.md), [002](./002-profile-and-public-profiles.md)
