# Result: feed-image-viewer

## Status

Complete (including fullscreen pinch-zoom follow-up).

## Implemented

- Fullscreen overlay with backdrop (`z-200`), **`object-contain`** preview inside the overlay, Telegram UI close `IconButton`, Escape, backdrop tap.
- **Pinch-zoom (2026-05-25):** the image-area control uses **`touch-manipulation`** (`touch-action: manipulation`) instead of **`touch-pan-y`** (**`touch-action: pan-y`**, which disables browser pinch-zoom on WebKit / Telegram Mini App webviews).
- **Primary imagery** (**`FeedCard`** poster, **`FeedPostCard`** attachment via `FeedOpenableContainedImage`, **`MovieCardDetailPage`** hero) uses a **full-bleed** layout: **`img`** as **`block`**, **`w-full`**, **`h-auto`**, **`max-w-none`** so **width spans the tile** and **height follows intrinsic aspect ratio** — **no empty side gutters or letterboxing inside the image region**. No stretching (`object-cover` / `object-contain`) on these heroes; cropping is avoided in-feed; **fullscreen overlay** keeps **`object-contain`** for full view.
- Referenced-card **thumbnail** in **`FeedPostCard`** remains a small fixed box with **`object-cover`**.
- Optional **`backdropFill`** / **`FeedContainedImageBackdrop`** remain for **`object-contain`** thumbnails and nested surfaces (`FeedOpenableContainedImage`).
- `useFullscreenImageActivator` coordinates deferred navigation (`~280–330ms`) with double-click / double-tap fullscreen open.
- Feed movie card posters use programmatic navigation so doubles do not navigate on the first click.
- Feed post images defer navigation when the post row is clickable; thumbnails inside `<Link>` use a presentation-only hit target + double activation for fullscreen without breaking nested link semantics.
- Card detail poster wired to fullscreen on double activation (single tap unchanged: no navigation).

## Files touched

- `frontend/src/components/media/FullscreenImageOverlay.tsx` — **`touch-manipulation`**, docstring on pinch-zoom rationale
- `frontend/src/components/media/FullscreenImageOverlay.test.tsx` (new) — class regression guard
- `frontend/src/test/setup.ts` (new) — jest-dom matchers for Vitest
- `frontend/vitest.config.ts` (new)
- `frontend/package.json` — `npm run test`; devDependencies Vitest / RTL / jsdom / `@testing-library/dom`
- `frontend/eslint.config.js` — lint **`vitest.config.ts`** without type-aware project coupling
- `.cursor/features/feed-image-viewer/feature.md`
- `.cursor/active/feed-image-viewer/{plan,progress,result}.md`
- `docs/features/feed-image-viewer.md`
- `.cursor/memory/logs/action-log.md` (+ new log fragment)

## Verification

```bash
cd frontend && npm run lint && npm run test && npm run build
```

- ESLint: pass  
- Vitest (`FullscreenImageOverlay` touch-action contract): pass  
- `tsc -b` + `vite build`: pass  

## Notes / limitations

- Single navigation on imagery is intentionally deferred (~280ms) wherever deferred navigation pairs with fullscreen, so doubles can cancel it; UX trade-off required to keep `<Link>` wrappers correct.
- Very fast triple interactions may still feel platform-specific; touch double-tap uses a ~330ms window.
- Very tall posters increase card height in the feed and on card detail; users rely on scroll. Fullscreen overlay still shows the full uncropped image.
