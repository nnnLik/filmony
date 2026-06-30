## 2026-06-30T10:47:25Z — scroll-restore — code

- Summary: Implemented global scroll restore with route-keyed storage, provider wiring, feed integration, tests, lint/build.

- Feature slug: `scroll-restore`

- Action type: `code`

### Files

- `frontend/src/App.tsx`
- `frontend/src/features/scrollRestore/ScrollRestoreProvider.tsx`
- `frontend/src/features/scrollRestore/__tests__/integration.test.tsx`
- `frontend/src/features/scrollRestore/__tests__/routeKey.test.ts`
- `frontend/src/features/scrollRestore/__tests__/service.test.ts`
- `frontend/src/features/scrollRestore/__tests__/storage.test.ts`
- `frontend/src/features/scrollRestore/containers.ts`
- `frontend/src/features/scrollRestore/flags.ts`
- `frontend/src/features/scrollRestore/index.ts`
- `frontend/src/features/scrollRestore/metrics.ts`
- `frontend/src/features/scrollRestore/routeKey.ts`
- `frontend/src/features/scrollRestore/service.ts`
- `frontend/src/features/scrollRestore/storage.ts`
- `frontend/src/lib/__tests__/feedScrollRestore.test.ts`
- `frontend/src/lib/feedScrollRestore.ts`
- `frontend/src/pages/FeedPage.tsx`
- `.cursor/active/scroll-restore/plan.md`
- `.cursor/active/scroll-restore/progress.md`
- `.cursor/active/scroll-restore/result.md`
- `.cursor/features/scroll-restore/feature.md`
- `docs/features/scroll-restore.md`

### Verification

- `npm run test -- routeKey.test.ts` (pass)
- `npm run test -- storage.test.ts` (pass)
- `npm run test -- service.test.ts` (pass)
- `npm run test -- integration.test.tsx` (pass)
- `npm run test -- feedScrollRestore.test.ts` (pass)
- `npm run lint` (pass)
- `npm run build` (pass)
