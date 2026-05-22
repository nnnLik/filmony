# Feature: Feed & card fullscreen image viewer

## Summary

Users can **double-click** (desktop) or **double-tap** (touch) feed and card images to open a fullscreen preview overlay. Single activation keeps existing routing: movie cards navigate to `/cards/:id`, feed posts navigate when the row is linkable, and thumbnails nested inside anchors still perform their default navigation on ordinary taps.

## UX

In the feed list, **movie posters** and **post attachment previews** combine a softened, blurred duplicate of the image (`object-cover`, slightly scaled) under the crisp **`object-contain`** foreground layer. Letterboxing gutters read as tinted fill instead of hard empty bands, without distorting the sharp preview. Navigation and **fullscreen overlay** semantics are unchanged; the overlay still receives the canonical image URL via `useFullscreenImageActivator`.

| Surface | Single activation | Double activation |
|---------|-------------------|-------------------|
| Feed movie poster | Opens card (`fromFeed`) | Opens fullscreen overlay |
| Feed post attachment | Opens post (when `linkToDetail`) | Fullscreen overlay |
| Referenced card thumbnail in a post row | Follows the existing card link | Fullscreen overlay |
| Comment attachment chips | (no routing) | Fullscreen overlay |
| Card detail poster | none | Fullscreen overlay |

Close the overlay via **backdrop tap**, **`X`**, or **Escape**.

## Implementation map

| Piece | Responsibility |
|-------|----------------|
| [`frontend/src/components/media/FullscreenImageOverlay.tsx`](../../frontend/src/components/media/FullscreenImageOverlay.tsx) | Portal overlay, backdrop, close affordances |
| [`frontend/src/hooks/useFullscreenImageActivator.ts`](../../frontend/src/hooks/useFullscreenImageActivator.ts) | Double activation + deferred navigation timers |
| [`frontend/src/components/feed/FeedOpenableContainedImage.tsx`](../../frontend/src/components/feed/FeedOpenableContainedImage.tsx) | `object-contain` preview plus optional **`backdropFill`** (blur under-layer); wrappers for thumbnails vs navigable blobs |
| **`FeedContainedImageBackdrop`** (same module) | Building block: blurred fill + foreground `img` for ratio-locked regions (feed poster frame) |

## Verification

```bash
cd frontend && npm run lint && npm run build
```

## Related docs

- UI conventions overview: [`docs/frontend/ui-conventions.md`](../frontend/ui-conventions.md)
