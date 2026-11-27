# watch-leave-rate-create-flow — test/lint run

cwd: `frontend`

## Unit tests — PASS

Command:

```
npm test -- src/lib/__tests__/watchLeaveRatePrompt.test.ts
```

(`package.json` script: `"test": "vitest run"`)

Exit code: `0`

Output:

```
> frontend@0.0.0 test
> vitest run src/lib/__tests__/watchLeaveRatePrompt.test.ts

 RUN  v3.2.6 /Users/r.makkhmudov/Projects/github/filmony/frontend

 ✓ src/lib/__tests__/watchLeaveRatePrompt.test.ts (5 tests) 2ms

 Test Files  1 passed (1)
      Tests  5 passed (5)
   Start at  04:38:51
   Duration  743ms (transform 53ms, setup 65ms, collect 61ms, tests 2ms, environment 364ms, prepare 49ms)
```

## ESLint — PASS

Command:

```
npx eslint src/lib/watchLeaveRatePrompt.ts src/lib/__tests__/watchLeaveRatePrompt.test.ts src/pages/FilmWatchPage.tsx src/pages/FilmDetailPage.tsx
```

Exit code: `0`

No error or warning lines. Empty stdout.

Full build was not run (lint and tests passed).
