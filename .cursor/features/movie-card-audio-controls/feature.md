# Movie card audio controls — compact inline pattern

## Problem

Card-attached audio on the movie card detail view lived in a separate tags-panel subsection with a prominent uppercase heading (“Аудио к карточке”), adding vertical bulk and pushing primary card context down.

## Goal

- Inline, compact controls: **play** as the primary, one-tap action; **download** secondary and lower emphasis.
- Avoid a tall standalone “audio panel” — prefer poster-adjacent chrome with minimal extra scroll height.

## Acceptance criteria

- [x] No labeled standalone audio block in the tags section on card detail.
- [x] Play control is visually primary; download is visually secondary.
- [x] On poster, controls sit in a high-contrast frosted/dark capsule so they remain legible on varied poster imagery.
- [x] Playback and download behavior unchanged (same helpers / API paths).
- [x] Frontend lint and build pass on touched code.
