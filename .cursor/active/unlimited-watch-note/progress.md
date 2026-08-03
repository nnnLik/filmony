# unlimited-watch-note — progress

## Frontend (done)

- Removed `frontend/src/lib/watchNoteLimits.ts` (`MAX_WATCH_NOTE_LEN = 1000`).
- Create/edit card flows: `RatedCardScrollForm`, `CreateCardPage`, `EditMovieCardPage` — no `maxLength`, no submit blocking, no `.slice(0, 1000)` on payload.
- Watchlist note: `WatchlistForm` — same; submit no longer disabled by length.
- UI counters show current length only (no `/1000` denominator); hint copy no longer mentions character cap.
- Spoiler/reaction insert helpers (`insertSnippetAtCaret`, `toggleSpoilerAtSelection`) accept optional `maxLen`; watch-note callers omit it so tokens always insert.
- Updated `profileTypes.ts` JSDoc for `watch_note`.
