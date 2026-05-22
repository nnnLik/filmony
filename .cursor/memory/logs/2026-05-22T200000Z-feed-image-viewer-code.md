## 2026-05-22T200000Z — feed-image-viewer — code

- **Summary**: Feed and card-detail primary images use full card width with height from intrinsic aspect ratio (`block w-full h-auto max-w-none`); removed flex-centered `object-contain` + max-height caps that caused in-frame letterboxing. Fullscreen viewer and deferred single-tap navigation unchanged.
- **Files**:
  - `frontend/src/components/feed/FeedCard.tsx`
  - `frontend/src/components/feed/FeedPostCard.tsx`
  - `frontend/src/pages/MovieCardDetailPage.tsx`
  - `docs/features/feed-image-viewer.md`
  - `docs/frontend/ui-conventions.md`
  - `.cursor/active/feed-image-viewer/progress.md`
  - `.cursor/active/feed-image-viewer/result.md`
- **Verification**: `cd frontend && npm run lint && npm run build` (pass).
