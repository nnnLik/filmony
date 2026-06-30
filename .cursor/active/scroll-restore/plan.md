# Scroll Restore Plan

## Goal
Add scroll restore utilities, provider wiring, feed integration, and coverage.

## Plan
1. Define scroll restore utilities: route key builder, storage adapter, and restore service.
   - Key files: `frontend/src/lib/scrollRestore.ts`, `frontend/src/lib/scrollRestoreStorage.ts`,
     `frontend/src/lib/scrollRestoreService.ts`
2. Add a provider to wire scroll restore lifecycle and context.
   - Key files: `frontend/src/providers/ScrollRestoreProvider.tsx`,
     `frontend/src/providers/index.ts`
3. Integrate feed list with scroll restore so route changes persist and restore position.
   - Key files: `frontend/src/pages/FeedPage.tsx`, `frontend/src/components/feed/FeedList.tsx`
4. Add tests for utilities and provider integration.
   - Key files: `frontend/src/lib/__tests__/scrollRestore.test.ts`,
     `frontend/src/providers/__tests__/ScrollRestoreProvider.test.tsx`
5. Run lint/build checks for frontend.
   - Commands: `cd frontend && npm run lint`, `cd frontend && npm run build`

## Tests
- `cd frontend && npm run lint`
- `cd frontend && npm run build`
