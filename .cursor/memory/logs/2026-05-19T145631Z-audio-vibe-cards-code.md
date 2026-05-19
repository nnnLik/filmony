Timestamp: 2026-05-19T145631Z
Feature slug: audio-vibe-cards
Action type: code
Summary: Added shared feed audio playback for cards, including a persistent feed-level audio provider, compact feed-card controls, and a mute/unmute toggle next to the scroll-to-top FAB.
Files:
- `frontend/src/context/FeedCardGlobalAudioProvider.tsx`
- `frontend/src/context/feedCardGlobalAudioContext.ts`
- `frontend/src/hooks/useFeedCardGlobalAudio.ts`
- `frontend/src/components/feed/FeedCard.tsx`
- `frontend/src/components/feed/FeedTopFab.tsx`
- `frontend/src/components/cards/MovieCardAudioPlayer.tsx`
- `frontend/src/pages/FeedPage.tsx`
- `docs/features/audio-vibe-cards.md`
Verification:
- `cd frontend && npm run lint`
- `cd frontend && npm run build`
