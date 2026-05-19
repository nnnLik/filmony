- **Timestamp:** 2026-05-19T190000Z
- **Feature slug:** movie-card-audio-controls
- **Action type:** code

## Summary

Poster audio controls on movie card detail wrapped in a frosted dark capsule (`.filmony-detail-poster-audio-pill`); compact `MovieCardAudioPlayer` styling tuned for contrast (play ring/shadow, secondary glass-style send button, lighter status text on dark chrome).

## Files

- `frontend/src/pages/MovieCardDetailPage.tsx`
- `frontend/src/components/cards/MovieCardAudioPlayer.tsx`
- `frontend/src/index.css`

## Verification

- `cd frontend && npm run lint && npm run build` — success (exit 0)
