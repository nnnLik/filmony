# Movie card audio — compact inline controls

## Summary

Movie card **detail** view no longer uses a separate tags-panel block titled "Аудио к карточке". Playback and Telegram-send live in a **compact row** on the **poster overlay**, directly under the rating ring, inside a **`filmony-detail-poster-audio-pill`** frosted capsule (dark translucent fill, **backdrop-filter** blur, light rim, subtle mint-accent outline). **Play** stays primary (`IconButton` **bezeled**, larger, ring + shadow, stronger icon stroke); **send to Telegram** stays secondary (**gray**, smaller, faint glass-style fill).

## Components

- **`MovieCardAudioPlayer`** — `variant="compact"` on the poster: centered row inside the pill; compact status/error lines use higher-contrast tints aimed at the dark capsule. Default layout unchanged for reuse elsewhere.
- **`MovieCardRatingAudioVisualizer`** — `compact` slightly reduces canvas size and scales radial artwork so the visualization stays aligned with the ring.

## User-visible behavior

- Same audio URL resolution, playback, and Telegram send flow as before (`frontend/src/lib/movieCardAudioMedia.ts`, `postSendUserCardAudioToTelegram`).
- Less vertical scroll before tags / watch note content on cards with audio.

## Verification

```bash
cd frontend && npm run lint && npm run build
```
