## Timestamp
2026-05-22T13:41:30Z (UTC)

## Feature slug
feed-image-viewer

## Action type
code

## Summary
Added fullscreen overlay + activation hook, wired FeedCard posters/comments, FeedPost attachments/thumbnails, and MovieCardDetail poster/attachments; tightened embed sizing to `object-contain`.

## Files
- `frontend/src/components/media/FullscreenImageOverlay.tsx`
- `frontend/src/hooks/useFullscreenImageActivator.ts`
- `frontend/src/components/feed/FeedOpenableContainedImage.tsx`
- `frontend/src/components/feed/FeedCard.tsx`
- `frontend/src/components/feed/FeedPostCard.tsx`
- `frontend/src/pages/MovieCardDetailPage.tsx`

## Verification
`cd frontend && npm run lint && npm run build` (pass).
