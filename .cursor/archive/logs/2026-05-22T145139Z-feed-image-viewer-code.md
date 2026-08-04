## Timestamp

2026-05-22T145139Z

## Feature slug

feed-image-viewer

## Action type

code

## Summary

Filled feed list image gutters without distorting previews: blurred `object-cover` under-layer + sharp `object-contain` foreground for movie poster previews and navigable feed post attachments; exported `FeedContainedImageBackdrop`; optional `backdropFill` on `FeedOpenableContainedImage`.

## Files

- `frontend/src/components/feed/FeedOpenableContainedImage.tsx`
- `frontend/src/components/feed/FeedCard.tsx`
- `frontend/src/components/feed/FeedPostCard.tsx`
- `docs/features/feed-image-viewer.md`
- `docs/frontend/ui-conventions.md`
- `.cursor/active/feed-image-viewer/progress.md`
- `.cursor/active/feed-image-viewer/result.md`

## Verification

```bash
cd frontend && npm run lint && npm run build
```

Pass (ESLint + Vite production build).

