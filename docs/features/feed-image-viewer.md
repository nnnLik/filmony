# Feature: Feed & card fullscreen image viewer

## Summary

Users can **double-click** (desktop) or **double-tap** (touch) feed and card images to open a fullscreen preview overlay. Single activation keeps existing routing: movie cards navigate to `/cards/:id`, feed posts navigate when the row is linkable, and thumbnails nested inside anchors still perform their default navigation on ordinary taps.

## UX

Primary **movie posters**, **feed post attachments**, and the **card detail hero** use a **full-bleed preview block**: the bitmap is **`display: block`** with **`width: 100%`**, **`height: auto`**, and **`max-width: none`** so the **card reserves no fixed image slot** — **height follows the decoded aspect ratio** edge-to-edge (**no letterboxing inside the image region**). Images stay **non-distorted** (no `object-fit` stretch or crop on these surfaces). **`object-contain`** is reserved for the **fullscreen overlay** (full uncropped view) and smaller **thumbnail** surfaces (e.g. comment attachments, referenced-card chips) where fitting a fixed box matters. Navigation and **fullscreen overlay** semantics are unchanged; the overlay still receives the canonical image URL via `useFullscreenImageActivator`.

| Surface | Single activation | Double activation |
|---------|-------------------|-------------------|
| Feed movie poster | Opens card (`fromFeed`) | Opens fullscreen overlay |
| Feed post attachment | Opens post (when `linkToDetail`) | Fullscreen overlay |
| Referenced card thumbnail in a post row | Follows the existing card link | Fullscreen overlay |
| Comment attachment chips | (no routing) | Fullscreen overlay |
| Card detail poster | none | Fullscreen overlay |

Close the overlay via **backdrop tap**, **`X`**, or **Escape**.

On **touch**, the fullscreen image area uses **`touch-manipulation`** so the browser/WebView may handle **pinch-zoom** while still allowing normal panning (avoid **`touch-pan-y`** alone, which maps to **`touch-action: pan-y`** and disables pinch-zoom in WebKit-backed clients such as Telegram).

## Implementation map

| Piece | Responsibility |
|-------|----------------|
| [`frontend/src/components/media/FullscreenImageOverlay.tsx`](../../frontend/src/components/media/FullscreenImageOverlay.tsx) | Portal overlay, backdrop, close affordances |
| [`frontend/src/hooks/useFullscreenImageActivator.ts`](../../frontend/src/hooks/useFullscreenImageActivator.ts) | Double activation + deferred navigation timers |
| [`frontend/src/components/feed/FeedOpenableContainedImage.tsx`](../../frontend/src/components/feed/FeedOpenableContainedImage.tsx) | Openable thumbnails/attachments (`img` passes through Tailwind classes) |

## Verification

```bash
cd frontend && npm run lint && npm run test && npm run build
```

## Related docs

- UI conventions overview: [`docs/frontend/ui-conventions.md`](../frontend/ui-conventions.md)
