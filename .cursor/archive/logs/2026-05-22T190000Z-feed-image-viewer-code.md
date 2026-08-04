# Action log

- **Timestamp:** 2026-05-22T19:00:00Z
- **Feature slug:** feed-image-viewer
- **Action type:** code + docs

## Summary

Adaptive poster/media height: primary movie posters and feed post attachments size from intrinsic aspect ratio (`max-w-full` + `max-h` caps, `object-contain`, top bias) instead of fixed-height `object-cover` frames; detail hero aligns with same rules. Docs and active feature artifacts refreshed.

## Files

- `frontend/src/components/feed/FeedCard.tsx`
- `frontend/src/components/feed/FeedPostCard.tsx`
- `frontend/src/pages/MovieCardDetailPage.tsx`
- `docs/features/feed-image-viewer.md`
- `docs/frontend/ui-conventions.md`
- `.cursor/active/feed-image-viewer/progress.md`
- `.cursor/active/feed-image-viewer/result.md`

## Verification

```bash
cd frontend && npm run lint && npm run build
```

(Pass after change.)
