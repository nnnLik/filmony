# Plan: movie-card-audio-controls

1. **Player component** (`MovieCardAudioPlayer.tsx`): add `variant="compact"` — single tight row, play `IconButton` larger (`m`) + `bezeled`, download smaller (`s`) + `gray` + reduced opacity; optional `className`; compact error line with truncate.
2. **Visualizer** (`MovieCardRatingAudioVisualizer.tsx`): optional `compact` prop — slightly smaller canvas and scaled radial geometry so the glow still fits the rating ring overlay.
3. **Detail page** (`MovieCardDetailPage.tsx`): mount compact player under the rating overlay on the poster; pass `compact` to visualizer; remove the tags-panel “Аудио к карточке” block entirely.
4. **Verification**: `cd frontend && npm run lint && npm run build`.
5. **Docs & memory**: feature docs, active `progress.md` / `result.md`, action-log fragment + index line.
