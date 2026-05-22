# Progress: feed-image-viewer

- **2026-05-22** — Implemented `FullscreenImageOverlay`, `useFullscreenImageActivator`, `FeedOpenableContainedImage` wrappers.
- **2026-05-22** — Integrated viewers into `FeedCard`, `FeedPostCard`, `MovieCardDetailPage`; switched embeds to `object-contain` within bounds.
- **2026-05-22** — Ran `cd frontend && npm run lint && npm run build` (pass).
- **2026-05-22** — Authored `.cursor/features/`, `docs/features/feed-image-viewer.md`, updated action log index.
- **2026-05-22** — Feed list previews: blurred `object-cover` under-layer beneath `object-contain` foreground for `FeedCard` poster + feed post attachments (`backdropFill` / `FeedContainedImageBackdrop`); docs/UI conventions/action log refreshed; `frontend` lint/build pass.
- **2026-05-22** — **Cover-fill frames**: primary poster/media areas in `FeedCard`, `FeedPostCard` (attachment + referenced thumb), `MovieCardDetailPage` use fixed-height frames + **`object-cover`** (crop, no stretch); docs + memory log updated; **`cd frontend && npm run lint && npm run build`** pass.
- **2026-05-22** — **Poster framing tweak**: **`FeedCard`**, **`FeedPostCard`** (**`object-cover`** surfaces), **`MovieCardDetailPage`** hero — **`object-bottom`** focal alignment + modestly taller **`FeedCard`** poster frame; docs + memory log updated; **`cd frontend && npm run lint && npm run build`** pass.
- **2026-05-22** — **Poster framing (top-anchor)**: same surfaces — **`object-top`** focal alignment so the **upper** band of portrait posters stays visible; docs UI conventions/feature doc + memory log refreshed; **`cd frontend && npm run lint && npm run build`** pass.
- **2026-05-22** — **Adaptive poster height**: **`FeedCard`**, **`FeedPostCard`** attachments, **`MovieCardDetailPage`** hero — intrinsic aspect (`max-w-full w-auto`, **`object-contain object-top`**, **`max-height`** caps); docs + **`result.md`** + action log; **`cd frontend && npm run lint && npm run build`** pass.
- **2026-05-22** — **Full-width natural height (no in-frame letterboxing)**: **`FeedCard`** poster, **`FeedPostCard`** attachment, **`MovieCardDetailPage`** hero — **`block w-full h-auto max-w-none`** (height from bitmap aspect, edge-to-edge); docs + **`result.md`** + action log; **`cd frontend && npm run lint && npm run build`** pass.
