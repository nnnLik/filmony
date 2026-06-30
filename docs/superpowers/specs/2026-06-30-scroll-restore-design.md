# Global Scroll Restoration (Back Navigation)

## Goal
Provide consistent scroll restoration for list/feed screens when navigating back, restoring the previous scroll position across routes and handling async content safely.

## Context
Users expect returning to the same spot in lists/feeds after navigating away. Current behavior resets to top. The approved design is a global, route-based scroll restore with async content handling and a safe fallback to top.

## Approach
**Recommended**
- Implement a global scroll restoration service in the frontend.
- Store scroll position by route key on forward navigation/unmount.
- Restore position on back navigation using the router history action.
- Wait for async content (data + layout) before restoring; fall back to top when position is unavailable or invalid.

**Alternatives**
- Per-screen local hooks: more boilerplate, higher risk of inconsistent behavior.
- Browser-native `history.scrollRestoration`: insufficient control for async feeds and custom containers.
- Always restore last position regardless of navigation direction: causes surprises when going forward.

## Data/storage
- **Storage key strategy:** `scroll:{routeKey}` where `routeKey` is the normalized pathname plus stable query subset (e.g., list filters/search) and route params; exclude volatile params (timestamps, cursor tokens).
- Store `{ position, containerId, updatedAt }` in a global in-memory map with optional sessionStorage backing for page reload resilience.
- TTL: 30 minutes; evict oldest entries beyond a fixed cap (e.g., 50 routes).

## Flow
1. On route change, detect history action (`PUSH`, `REPLACE`, `POP`).
2. Before leaving a route, capture scroll position:
   - If a route-specific scroll container is registered, use its `scrollTop`.
   - Otherwise use `window.scrollY`.
3. On `POP` (back/forward), attempt restore:
   - Resolve target route key.
   - Wait for data + layout readiness (see async handling).
   - Restore scroll for the registered container or `window`.
4. If no stored position, restoration fails, or container is missing, scroll to top.

## Edge cases
- **Async content:** restore after data loaded and layout settled; retry a few frames (e.g., `requestAnimationFrame` loop up to 5 ticks) until `scrollHeight` >= target position or timeout.
- **Dynamic list length:** if target position exceeds current max, clamp to `scrollHeight - clientHeight`.
- **Container vs window:** default to `window` unless a screen registers a container; container registration should include a stable `containerId`.
- **Route changes with filters:** route key includes normalized filters to prevent restoring to mismatched content.
- **SSR/initial load:** do not restore on first load; only on `POP`.

## Testing
- Unit tests for key normalization and storage behavior (eviction, TTL, clamps).
- Integration tests for route navigation:
  - Scroll, navigate away, back → position restored.
  - Forward navigation → no restoration.
  - Async data load delay → restore after content ready.
  - Container-based scroll restoration.
  - No stored position or missing container → scrolls to top.
  - Shorter content on return → clamped to max scroll.
  - Session reload (if sessionStorage backing enabled) → restores from stored state.

## Rollout/metrics
- Log a lightweight metric on restore success/failure with route key (sampled).
- Roll out behind a feature flag with quick disable.
