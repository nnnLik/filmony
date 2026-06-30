# Scroll Restore

## Scope
- Preserve scroll position when navigating back from detail views to list views.
- Apply across feeds and other list-based pages.
- Use global scroll restore provider, container registration, and session storage restore.

## Non-goals
- Persist scroll position across browser restarts or new sessions.
- Add new UI controls or settings for scroll behavior.
- Implement per-route custom animations or transitions.

## Acceptance Criteria
- Returning from a detail view restores the previous scroll position in the originating list.
- Restoration works for feeds and other list-based pages using registered containers.
- Scroll positions are stored and restored via session storage through the global provider.
