# Progress: feed-image-viewer

- **2026-05-22** — Implemented `FullscreenImageOverlay`, `useFullscreenImageActivator`, `FeedOpenableContainedImage` wrappers.
- **2026-05-22** — Integrated viewers into `FeedCard`, `FeedPostCard`, `MovieCardDetailPage`; switched embeds to `object-contain` within bounds.
- **2026-05-22** — Ran `cd frontend && npm run lint && npm run build` (pass).
- **2026-05-22** — Authored `.cursor/features/`, `docs/features/feed-image-viewer.md`, updated action log index.
- **2026-05-22** — Feed list previews: blurred `object-cover` under-layer beneath `object-contain` foreground for `FeedCard` poster + feed post attachments (`backdropFill` / `FeedContainedImageBackdrop`); docs/UI conventions/action log refreshed; `frontend` lint/build pass.
