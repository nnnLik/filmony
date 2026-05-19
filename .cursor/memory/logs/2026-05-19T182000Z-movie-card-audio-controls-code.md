- **Timestamp:** 2026-05-19T182000Z
- **Feature slug:** movie-card-audio-controls
- **Action type:** code

## Summary

Compact inline movie-card audio controls on card detail (poster overlay); removed standalone tags-panel audio section. Added `compact` / `variant` options on visualizer and player.

## Files

- `frontend/src/components/cards/MovieCardAudioPlayer.tsx`
- `frontend/src/components/cards/MovieCardRatingAudioVisualizer.tsx`
- `frontend/src/pages/MovieCardDetailPage.tsx`

## Verification

- `cd frontend && npm run lint && npm run build` — success
