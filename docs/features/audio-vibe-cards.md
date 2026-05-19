# Audio vibe cards

## Summary
Users can attach one optional audio file to a card and manage it from the edit flow. Card detail still shows its own play/pause control, but the home feed now has a shared audio session so playback can keep going while the user scrolls through more cards.

## Feed playback
- `FeedPage` wraps the feed in `FeedCardGlobalAudioProvider`, which owns one hidden `<audio>` element and persists the enabled/disabled preference in `localStorage` under `filmony-feed-card-audio-enabled`.
- Feed cards with audio render a compact player wired to that shared session, so the active track survives re-renders and scrolling.
- `FeedTopFab` now stacks a volume mute/unmute control above the scroll-to-top / refresh button, so the user can stop or resume feed audio without leaving the list.
- Leaving the feed tab/page unmounts the provider and pauses the shared player; the provider also pauses when the browser tab is hidden.

## Detail playback
- The card detail page keeps its own local player and visualizer for the focused card view.
- Audio still uses the proxied API media URL so `<audio src>` does not require a Bearer header.

## Backend and media
- Audio storage stays in RustFS with `audio_url` on the card record.
- Upload, replace, delete, and media proxy behavior remain unchanged from the original `audio-vibe-cards` feature.

## Verification
- Frontend `npm run lint`
- Frontend `npm run build`
