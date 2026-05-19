# Movie card audio — compact inline controls

## Summary

Movie card **detail** view no longer uses a separate tags-panel block titled “Аудио к карточке”. Playback and download live in a **compact inline row** on the **poster overlay**, directly under the rating ring: **play** is the primary control (`IconButton` `bezeled`, larger); **download** is secondary (`gray`, smaller).

## Components

- **`MovieCardAudioPlayer`** — `variant="compact"` for poster overlay; default variant keeps the previous relaxed layout for any future reuse.
- **`MovieCardRatingAudioVisualizer`** — `compact` slightly reduces canvas size and scales radial artwork so the visualization stays aligned with the ring.

## User-visible behavior

- Same audio URL resolution, playback, and authenticated blob download as before (`frontend/src/lib/movieCardAudioMedia.ts`).
- Less vertical scroll before tags / watch note content on cards with audio.

## Verification

```bash
cd frontend && npm run lint && npm run build
```
