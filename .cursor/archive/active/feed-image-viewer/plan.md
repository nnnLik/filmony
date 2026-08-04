# Plan: feed-image-viewer

1. **`FullscreenImageOverlay`**: portal, body scroll lock, backdrop + image `object-contain`, IconButton close, Escape.
2. **`useFullscreenImageActivator`**: mouse `detail` (single vs multi-click) + touch double-tap timing; deferred `onSingleNavigate` when fullscreen URL exists so doubles cancel navigation.
3. **`FeedOpenableContainedImage`** (+ thumbnail variant nested in links with `presentation`/`aria-hidden`) for repeatable feed surfaces.
4. Wire **FeedCard** poster (`Link` → deferred `navigate` + overlay), comment attachments.
5. Wire **FeedPostCard** embedded image (+ deferred post navigation when `linkToDetail`) and referenced card thumbnail (`navigate` unchanged on single tap).
6. Wire **MovieCardDetailPage** poster + comment/draft previews (`object-contain`).
7. Run `frontend` lint/build; refresh feature/workflow docs and action-log entries.
8. **Pinch-zoom in overlay:** `FullscreenImageOverlay` must not set `touch-action` to values that block pinch-zoom (e.g. avoid bare `pan-y`); prefer `touch-manipulation` on the image-area control; add Vitest regression for the class contract; run `npm run test`.
