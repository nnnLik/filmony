# Feed & card fullscreen image viewer

## Scope

- Fullscreen overlay to preview feed and movie-card imagery without leaving the scroll context.
- **Single** click/tap preserves existing routing (feed movie card → detail, feed post → post, referenced card snippets → card, thumbnails inside `<Link>` keep default navigation).
- **Double** activation on the image (double-click on desktop / double-tap on touch where supported) opens a modal fullscreen viewer (`object-contain`, backdrop, Escape/close/button).

## Acceptance criteria

- Feed movie card posters and attachment images in expanded comments open the viewer on double activation; single activation still navigates or stays unchanged where there was navigation before.
- Feed post embedded images (and referenced card thumbnails inside post rows) behave the same relative to existing navigation.
- Movie card detail hero poster and comment/draft attachments open on double activation; bounded `object-contain` preview frames (no visual overflow cropping in card chrome).
- Overlay: dark backdrop, large contained image, close via X, Escape, tapping backdrop.
- `npm run lint` and `npm run build` succeed in `frontend/`.
