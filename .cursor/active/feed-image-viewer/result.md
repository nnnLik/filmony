# Result: feed-image-viewer

## Status

Complete.

## Implemented

- Fullscreen overlay with backdrop (`z-200`), **`object-contain`** preview inside the overlay, Telegram UI close `IconButton`, Escape, backdrop tap.
- Feed and detail **list previews** use fixed frames with **`object-cover`**: **`FeedCard`** poster `h-[min(52vw,14rem)] sm:h-64`; **`FeedPostCard`** attachment `h-[min(70vw,18rem)]`; referenced-card thumbnail in post row **`object-cover`** in its fixed thumb box; **`MovieCardDetailPage`** hero `h-[min(92vw,560px)]`. Uniform scale — crops edges when aspect mismatches — no gutters inside those frames.
- Optional **`backdropFill`** / **`FeedContainedImageBackdrop`** remain for thumbnails and other **`object-contain`** surfaces (`FeedOpenableContainedImage`).
- `useFullscreenImageActivator` coordinates deferred navigation (`~280–330ms`) with double-click / double-tap fullscreen open.
- Feed movie card posters use programmatic navigation so doubles do not navigate on the first click.
- Feed post images defer navigation when the post row is clickable; thumbnails inside `<Link>` use a presentation-only hit target + double activation for fullscreen without breaking nested link semantics.
- Card detail poster wired to fullscreen on double activation (single tap unchanged: no navigation).

## Files touched

- `frontend/src/components/media/FullscreenImageOverlay.tsx` (new)
- `frontend/src/hooks/useFullscreenImageActivator.ts` (new)
- `frontend/src/components/feed/FeedOpenableContainedImage.tsx` (backdrop stack + optional `backdropFill`)
- `frontend/src/components/feed/FeedCard.tsx`
- `frontend/src/components/feed/FeedPostCard.tsx`
- `frontend/src/pages/MovieCardDetailPage.tsx`
- `.cursor/features/feed-image-viewer/feature.md`
- `.cursor/active/feed-image-viewer/{plan,progress,result}.md`
- `docs/features/feed-image-viewer.md`
- `docs/frontend/ui-conventions.md`
- `.cursor/memory/logs/*` (+ index), including `2026-05-22T160500Z-feed-image-viewer-code.md`

## Verification

```bash
cd frontend && npm run lint && npm run build
```

- ESLint: pass (2026-05-22 after cover-fill frames)
- `tsc -b` + `vite build`: pass

Frontend has no bundled test runner; no automated UI tests added.

## Notes / limitations

- Single navigation on imagery is intentionally deferred (~280ms) wherever deferred navigation pairs with fullscreen, so doubles can cancel it; UX trade-off required to keep `<Link>` wrappers correct.
- Very fast triple interactions may still feel platform-specific; touch double-tap uses a ~330ms window.
- **`object-cover`** on list previews crops at frame edges; fullscreen overlay keeps full image without cropping via **`object-contain`** there.
