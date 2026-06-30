# Scroll Restore

## Overview
The scroll restore feature preserves the user's scroll position when navigating
between views so returning to a list or feed feels seamless. It focuses on
restoring context for long lists without forcing users to re-scroll.

## Behavior
- Saves scroll position when a supported view unmounts or navigation occurs.
- Restores the last saved position when the user returns to the same view.
- Falls back to the top of the page if no saved position exists.
- Resets stored position when the underlying dataset changes significantly
  (for example, a new filter or query is applied).

## Configuration
- Enable or disable scroll restore per route or view.
- Use a stable restore key that includes route params or query state so
  different list contexts do not overwrite each other.
- Optional: configure a maximum age for stored positions to avoid stale
  restores after long inactivity.

## Key Components
- Scroll position storage (in-memory or session-based) keyed by view context.
- Navigation hooks that capture position before route changes.
- Restore logic that applies the stored position after content is ready.

## Testing
- Navigate away from a long list and return; position should be restored.
- Change filters/search; return should start at top.
- Refresh or hard reload; confirm expected reset or persistence behavior
  based on the configured storage.

## Limitations
- Restoration depends on content height; major layout changes may shift
  the exact position.
- Virtualized lists may require additional coordination to restore correctly.
