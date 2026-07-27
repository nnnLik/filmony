# Comment Header Actions Overflow

## Goal
Compact comment header actions: Reply icon plus overflow menu (Edit / Delete / To-feed) instead of inline text links; hide taste-match % on the viewer's own comments.

## Scope
- New `CommentHeaderActions` component (Reply `IconButton` + ⋯ overflow for owner actions).
- Movie card and feed post comment threads on detail pages.
- Taste quiz author badge: no % shown when the comment author is the current user.
- Feed card comment previews where header actions apply.

## Acceptance Criteria
- Reply is a visible icon control; owner Edit / Delete / To-feed live in a ⋯ overflow menu.
- Overflow menu shows only actions the user is allowed to perform (same rules as before).
- Own comments do not show taste-match percentage badge.
- Behavior unchanged on `MovieCardDetailPage` and `FeedPostDetailPage` aside from the new layout.

## Out of Scope
- Backend or API changes.
- Comment actions on list/feed surfaces beyond existing wiring.
- New automated frontend tests (follow-up if desired).
