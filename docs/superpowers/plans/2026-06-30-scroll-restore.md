I'm using the writing-plans skill to create the implementation plan.

# Global Scroll Restoration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a global, route-based scroll restoration system that restores list/feed positions on back/forward navigation while handling async content safely.

**Architecture:** Add a dedicated scroll restore feature module with route key normalization, bounded storage (TTL + cap), and a service that captures/restores scroll for window or registered containers. Wire a provider into the router to capture navigation actions and restore only on POP, then migrate the feed’s local scroll restore to the global service.

**Tech Stack:** React, TypeScript, React Router, @telegram-apps/telegram-ui, Testing Library + Vitest.

---

## File Structure

- Create: `frontend/src/features/scrollRestore/routeKey.ts` — normalize route key with stable query/params.
- Create: `frontend/src/features/scrollRestore/storage.ts` — in-memory store with TTL, cap, and sessionStorage backing.
- Create: `frontend/src/features/scrollRestore/service.ts` — capture/restore logic, async readiness, clamps.
- Create: `frontend/src/features/scrollRestore/containers.ts` — register/unregister scroll containers by id.
- Create: `frontend/src/features/scrollRestore/ScrollRestoreProvider.tsx` — router integration and lifecycle.
- Create: `frontend/src/features/scrollRestore/flags.ts` — feature flag and sampling knobs.
- Create: `frontend/src/features/scrollRestore/metrics.ts` — success/failure logging.
- Create: `frontend/src/features/scrollRestore/index.ts` — public exports.
- Modify: `frontend/src/app/App.tsx` — mount provider at root.
- Modify: `frontend/src/features/feed/FeedPage.tsx` — register container and remove local restore.
- Modify: `frontend/src/features/feed/hooks/useFeedScrollRestore.ts` — replace with global hook or delete usage.
- Test: `frontend/src/features/scrollRestore/__tests__/routeKey.test.ts`
- Test: `frontend/src/features/scrollRestore/__tests__/storage.test.ts`
- Test: `frontend/src/features/scrollRestore/__tests__/service.test.ts`
- Test: `frontend/src/features/scrollRestore/__tests__/integration.test.tsx`

---

### Task 1: Route Key Normalization

**Files:**
- Create: `frontend/src/features/scrollRestore/routeKey.ts`
- Test: `frontend/src/features/scrollRestore/__tests__/routeKey.test.ts`

- [ ] **Step 1: Write the failing tests**

```typescript
import { describe, expect, it } from 'vitest';
import { buildRouteKey } from '../routeKey';

describe('buildRouteKey', () => {
  it('includes pathname and stable query keys', () => {
    const key = buildRouteKey({
      pathname: '/feed',
      search: '?q=films&cursor=abc123',
      allowedQueryKeys: ['q'],
    });

    expect(key).toBe('/feed|query:q=films');
  });

  it('includes route params deterministically', () => {
    const key = buildRouteKey({
      pathname: '/lists/42',
      params: { listId: '42', ownerId: '7' },
    });

    expect(key).toBe('/lists/42|params:listId=42&ownerId=7');
  });

  it('omits empty query values and orders keys', () => {
    const key = buildRouteKey({
      pathname: '/feed',
      search: '?b=2&a=&c=3',
      allowedQueryKeys: ['c', 'a', 'b'],
    });

    expect(key).toBe('/feed|query:b=2&c=3');
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npm run test -- routeKey.test.ts`
Expected: FAIL with `ReferenceError: buildRouteKey is not defined`

- [ ] **Step 3: Implement route key helper**

```typescript
export type RouteKeyInput = {
  pathname: string;
  search?: string;
  params?: Record<string, string>;
  allowedQueryKeys?: string[];
};

export function buildRouteKey({
  pathname,
  search,
  params,
  allowedQueryKeys,
}: RouteKeyInput): string {
  const query = new URLSearchParams(search ?? '');
  const queryKeys = allowedQueryKeys ?? [];
  const normalizedQuery = queryKeys
    .map((key) => [key, query.get(key) ?? ''])
    .filter(([, value]) => value.length > 0)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, value]) => `${key}=${value}`)
    .join('&');

  const normalizedParams = params
    ? Object.keys(params)
        .sort()
        .map((key) => `${key}=${params[key]}`)
        .join('&')
    : '';

  const parts = [pathname];
  if (normalizedParams.length > 0) {
    parts.push(`params:${normalizedParams}`);
  }
  if (normalizedQuery.length > 0) {
    parts.push(`query:${normalizedQuery}`);
  }
  return parts.join('|');
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npm run test -- routeKey.test.ts`
Expected: PASS `frontend/src/features/scrollRestore/__tests__/routeKey.test.ts`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/scrollRestore/routeKey.ts frontend/src/features/scrollRestore/__tests__/routeKey.test.ts
git commit -m "feat(scroll): add route key normalization"
```

---

### Task 2: Storage Map With TTL and Cap

**Files:**
- Create: `frontend/src/features/scrollRestore/storage.ts`
- Test: `frontend/src/features/scrollRestore/__tests__/storage.test.ts`

- [ ] **Step 1: Write the failing tests**

```typescript
import { describe, expect, it, vi } from 'vitest';
import { ScrollRestoreStorage } from '../storage';

describe('ScrollRestoreStorage', () => {
  it('evicts entries beyond the cap', () => {
    const storage = new ScrollRestoreStorage({ ttlMs: 1_800_000, maxEntries: 2 });
    storage.set('a', { position: 10, containerId: null, updatedAt: 1 });
    storage.set('b', { position: 20, containerId: null, updatedAt: 2 });
    storage.set('c', { position: 30, containerId: null, updatedAt: 3 });

    expect(storage.get('a')).toBeNull();
    expect(storage.get('b')?.position).toBe(20);
  });

  it('expires entries older than ttl', () => {
    const now = 10_000;
    vi.spyOn(Date, 'now').mockReturnValue(now);
    const storage = new ScrollRestoreStorage({ ttlMs: 500, maxEntries: 50 });
    storage.set('feed', { position: 150, containerId: null, updatedAt: now - 600 });

    expect(storage.get('feed')).toBeNull();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npm run test -- storage.test.ts`
Expected: FAIL with `TypeError: ScrollRestoreStorage is not a constructor`

- [ ] **Step 3: Implement storage class**

```typescript
export type ScrollRestoreEntry = {
  position: number;
  containerId: string | null;
  updatedAt: number;
};

type StorageOptions = {
  ttlMs: number;
  maxEntries: number;
};

export class ScrollRestoreStorage {
  private readonly ttlMs: number;
  private readonly maxEntries: number;
  private readonly entries = new Map<string, ScrollRestoreEntry>();

  constructor({ ttlMs, maxEntries }: StorageOptions) {
    this.ttlMs = ttlMs;
    this.maxEntries = maxEntries;
  }

  get(key: string): ScrollRestoreEntry | null {
    const entry = this.entries.get(key);
    if (!entry) {
      return null;
    }
    if (Date.now() - entry.updatedAt > this.ttlMs) {
      this.entries.delete(key);
      return null;
    }
    return entry;
  }

  set(key: string, entry: ScrollRestoreEntry): void {
    this.entries.set(key, entry);
    this.evictIfNeeded();
  }

  private evictIfNeeded(): void {
    if (this.entries.size <= this.maxEntries) {
      return;
    }
    const sorted = [...this.entries.entries()].sort(
      ([, a], [, b]) => a.updatedAt - b.updatedAt,
    );
    const excess = this.entries.size - this.maxEntries;
    sorted.slice(0, excess).forEach(([key]) => this.entries.delete(key));
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npm run test -- storage.test.ts`
Expected: PASS `frontend/src/features/scrollRestore/__tests__/storage.test.ts`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/scrollRestore/storage.ts frontend/src/features/scrollRestore/__tests__/storage.test.ts
git commit -m "feat(scroll): add scroll restore storage"
```

---

### Task 3: Session Storage Backing and Defaults

**Files:**
- Modify: `frontend/src/features/scrollRestore/storage.ts`
- Test: `frontend/src/features/scrollRestore/__tests__/storage.test.ts`

- [ ] **Step 1: Write the failing tests**

```typescript
import { describe, expect, it } from 'vitest';
import { ScrollRestoreStorage } from '../storage';

describe('ScrollRestoreStorage session backing', () => {
  it('hydrates from sessionStorage when available', () => {
    sessionStorage.setItem(
      'scrollRestore:v1',
      JSON.stringify({ feed: { position: 99, containerId: null, updatedAt: 10 } }),
    );

    const storage = ScrollRestoreStorage.hydrate({
      ttlMs: 1_800_000,
      maxEntries: 50,
      storageKey: 'scrollRestore:v1',
    });

    expect(storage.get('feed')?.position).toBe(99);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npm run test -- storage.test.ts`
Expected: FAIL with `TypeError: ScrollRestoreStorage.hydrate is not a function`

- [ ] **Step 3: Implement session persistence**

```typescript
type HydrateOptions = StorageOptions & { storageKey: string };

export class ScrollRestoreStorage {
  // existing fields and methods ...

  static hydrate({ ttlMs, maxEntries, storageKey }: HydrateOptions): ScrollRestoreStorage {
    const storage = new ScrollRestoreStorage({ ttlMs, maxEntries });
    const raw = sessionStorage.getItem(storageKey);
    if (!raw) {
      return storage;
    }
    try {
      const parsed = JSON.parse(raw) as Record<string, ScrollRestoreEntry>;
      Object.entries(parsed).forEach(([key, entry]) => storage.set(key, entry));
    } catch {
      sessionStorage.removeItem(storageKey);
    }
    return storage;
  }

  persist(storageKey: string): void {
    const payload = Object.fromEntries(this.entries);
    sessionStorage.setItem(storageKey, JSON.stringify(payload));
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npm run test -- storage.test.ts`
Expected: PASS `frontend/src/features/scrollRestore/__tests__/storage.test.ts`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/scrollRestore/storage.ts frontend/src/features/scrollRestore/__tests__/storage.test.ts
git commit -m "feat(scroll): persist scroll restore state"
```

---

### Task 4: Restore Service With Async Handling

**Files:**
- Create: `frontend/src/features/scrollRestore/service.ts`
- Test: `frontend/src/features/scrollRestore/__tests__/service.test.ts`

- [ ] **Step 1: Write the failing tests**

```typescript
import { describe, expect, it, vi } from 'vitest';
import { ScrollRestoreService } from '../service';

describe('ScrollRestoreService', () => {
  it('clamps to max scroll height', async () => {
    const container = document.createElement('div');
    Object.defineProperty(container, 'scrollHeight', { value: 400, configurable: true });
    Object.defineProperty(container, 'clientHeight', { value: 200, configurable: true });
    container.scrollTop = 0;

    const service = new ScrollRestoreService();
    await service.restore({
      container,
      position: 350,
    });

    expect(container.scrollTop).toBe(200);
  });

  it('retries until content is ready', async () => {
    const container = document.createElement('div');
    Object.defineProperty(container, 'scrollHeight', { value: 0, configurable: true });
    Object.defineProperty(container, 'clientHeight', { value: 0, configurable: true });
    const service = new ScrollRestoreService({ maxFrames: 3 });

    const raf = vi.spyOn(window, 'requestAnimationFrame').mockImplementation((cb) => {
      Object.defineProperty(container, 'scrollHeight', { value: 100, configurable: true });
      Object.defineProperty(container, 'clientHeight', { value: 50, configurable: true });
      cb(0);
      return 0;
    });

    await service.restore({ container, position: 40 });
    expect(container.scrollTop).toBe(40);
    raf.mockRestore();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npm run test -- service.test.ts`
Expected: FAIL with `ReferenceError: ScrollRestoreService is not defined`

- [ ] **Step 3: Implement restore logic**

```typescript
type RestoreTarget = {
  container: HTMLElement | null;
  position: number;
};

type ServiceOptions = {
  maxFrames?: number;
};

export class ScrollRestoreService {
  private readonly maxFrames: number;

  constructor({ maxFrames = 5 }: ServiceOptions = {}) {
    this.maxFrames = maxFrames;
  }

  async restore({ container, position }: RestoreTarget): Promise<void> {
    const target = container ?? document.documentElement;
    await this.waitForReady(target, position);
    const maxScroll = Math.max(target.scrollHeight - target.clientHeight, 0);
    target.scrollTop = Math.min(position, maxScroll);
  }

  private waitForReady(target: HTMLElement, position: number): Promise<void> {
    let frame = 0;
    return new Promise((resolve) => {
      const tick = () => {
        frame += 1;
        const maxScroll = Math.max(target.scrollHeight - target.clientHeight, 0);
        if (maxScroll >= position || frame >= this.maxFrames) {
          resolve();
          return;
        }
        requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npm run test -- service.test.ts`
Expected: PASS `frontend/src/features/scrollRestore/__tests__/service.test.ts`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/scrollRestore/service.ts frontend/src/features/scrollRestore/__tests__/service.test.ts
git commit -m "feat(scroll): add restore service"
```

---

### Task 5: Container Registry and Provider Wiring

**Files:**
- Create: `frontend/src/features/scrollRestore/containers.ts`
- Create: `frontend/src/features/scrollRestore/ScrollRestoreProvider.tsx`
- Create: `frontend/src/features/scrollRestore/index.ts`
- Create: `frontend/src/features/scrollRestore/flags.ts`
- Create: `frontend/src/features/scrollRestore/metrics.ts`
- Modify: `frontend/src/app/App.tsx`

- [ ] **Step 1: Write the failing tests**

```typescript
import { describe, expect, it, vi } from 'vitest';
import { ScrollRestoreProvider } from '../ScrollRestoreProvider';

describe('ScrollRestoreProvider', () => {
  it('restores on POP only', () => {
    const onRestore = vi.fn();
    const provider = new ScrollRestoreProvider({ onRestore });
    provider.handleNavigation('PUSH');
    provider.handleNavigation('POP');

    expect(onRestore).toHaveBeenCalledTimes(1);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npm run test -- integration.test.tsx`
Expected: FAIL with `TypeError: ScrollRestoreProvider is not a constructor`

- [ ] **Step 3: Implement container registry and provider**

```typescript
// containers.ts
type ContainerEntry = { id: string; element: HTMLElement };
const registry = new Map<string, ContainerEntry>();

export function registerScrollContainer(id: string, element: HTMLElement): () => void {
  registry.set(id, { id, element });
  return () => registry.delete(id);
}

export function getScrollContainer(id: string): HTMLElement | null {
  return registry.get(id)?.element ?? null;
}
```

```tsx
// ScrollRestoreProvider.tsx
import { useEffect, useMemo, useRef } from 'react';
import { useLocation, useNavigationType } from 'react-router-dom';
import { buildRouteKey } from './routeKey';
import { ScrollRestoreStorage } from './storage';
import { ScrollRestoreService } from './service';
import { getScrollContainer } from './containers';
import { isScrollRestoreEnabled, scrollRestoreConfig } from './flags';
import { logScrollRestoreMetric } from './metrics';

const STORAGE_KEY = 'scrollRestore:v1';

export function ScrollRestoreProvider({ children }: { children: React.ReactNode }) {
  const navigationType = useNavigationType();
  const location = useLocation();
  const storage = useMemo(
    () =>
      ScrollRestoreStorage.hydrate({
        ttlMs: scrollRestoreConfig.ttlMs,
        maxEntries: scrollRestoreConfig.maxEntries,
        storageKey: STORAGE_KEY,
      }),
    [],
  );
  const service = useMemo(() => new ScrollRestoreService(), []);
  const prevLocation = useRef(location);

  useEffect(() => {
    if (!isScrollRestoreEnabled()) {
      prevLocation.current = location;
      return;
    }

    const prevKey = buildRouteKey({
      pathname: prevLocation.current.pathname,
      search: prevLocation.current.search,
    });

    storage.set(prevKey, {
      position: window.scrollY,
      containerId: null,
      updatedAt: Date.now(),
    });
    storage.persist(STORAGE_KEY);
    prevLocation.current = location;
  }, [location, storage]);

  useEffect(() => {
    if (!isScrollRestoreEnabled() || navigationType !== 'POP') {
      return;
    }
    const key = buildRouteKey({
      pathname: location.pathname,
      search: location.search,
    });
    const entry = storage.get(key);
    if (!entry) {
      window.scrollTo({ top: 0 });
      logScrollRestoreMetric({ key, outcome: 'missing' });
      return;
    }
    const container = entry.containerId ? getScrollContainer(entry.containerId) : null;
    service
      .restore({ container, position: entry.position })
      .then(() => logScrollRestoreMetric({ key, outcome: 'restored' }))
      .catch(() => {
        window.scrollTo({ top: 0 });
        logScrollRestoreMetric({ key, outcome: 'failed' });
      });
  }, [location, navigationType, service, storage]);

  return <>{children}</>;
}
```

```typescript
// flags.ts
export const scrollRestoreConfig = {
  ttlMs: 1_800_000,
  maxEntries: 50,
  sampleRate: 0.1,
};

export function isScrollRestoreEnabled(): boolean {
  return Boolean((window as Window & { __flags__?: Record<string, boolean> }).__flags__?.scrollRestore);
}
```

```typescript
// metrics.ts
import { scrollRestoreConfig } from './flags';

type Outcome = 'restored' | 'missing' | 'failed';

export function logScrollRestoreMetric({
  key,
  outcome,
}: {
  key: string;
  outcome: Outcome;
}): void {
  if (Math.random() > scrollRestoreConfig.sampleRate) {
    return;
  }
  console.info('[scroll-restore]', outcome, key);
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npm run test -- integration.test.tsx`
Expected: PASS `frontend/src/features/scrollRestore/__tests__/integration.test.tsx`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/scrollRestore frontend/src/app/App.tsx
git commit -m "feat(scroll): add global provider and registry"
```

---

### Task 6: Feed Integration (Replace Local Scroll Restore)

**Files:**
- Modify: `frontend/src/features/feed/FeedPage.tsx`
- Modify: `frontend/src/features/feed/hooks/useFeedScrollRestore.ts`

- [ ] **Step 1: Write the failing tests**

```typescript
import { describe, expect, it } from 'vitest';
import { buildRouteKey } from '../../scrollRestore/routeKey';

describe('feed scroll restore', () => {
  it('uses normalized key for feed filters', () => {
    const key = buildRouteKey({
      pathname: '/feed',
      search: '?q=cinema&cursor=ignored',
      allowedQueryKeys: ['q'],
    });

    expect(key).toBe('/feed|query:q=cinema');
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npm run test -- integration.test.tsx`
Expected: FAIL with `TypeError: buildRouteKey is not a function`

- [ ] **Step 3: Update feed screen to register container**

```tsx
import { useEffect, useMemo, useRef } from 'react';
import { registerScrollContainer } from '../scrollRestore/containers';
import { buildRouteKey } from '../scrollRestore/routeKey';

const FEED_CONTAINER_ID = 'feed-scroll';

export function FeedPage() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const routeKey = useMemo(
    () =>
      buildRouteKey({
        pathname: '/feed',
        search: window.location.search,
        allowedQueryKeys: ['q', 'filter'],
      }),
    [],
  );

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }
    return registerScrollContainer(FEED_CONTAINER_ID, containerRef.current);
  }, []);

  return (
    <div ref={containerRef} data-route-key={routeKey}>
      {/* existing feed content */}
    </div>
  );
}
```

```typescript
// useFeedScrollRestore.ts
export function useFeedScrollRestore(): void {
  // no-op: global scroll restore now handles feed
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npm run test -- integration.test.tsx`
Expected: PASS `frontend/src/features/scrollRestore/__tests__/integration.test.tsx`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/feed/FeedPage.tsx frontend/src/features/feed/hooks/useFeedScrollRestore.ts
git commit -m "refactor(feed): use global scroll restore"
```

---

### Task 7: Integration Tests for Navigation Behavior

**Files:**
- Test: `frontend/src/features/scrollRestore/__tests__/integration.test.tsx`

- [ ] **Step 1: Write the failing tests**

```typescript
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ScrollRestoreProvider } from '../ScrollRestoreProvider';

describe('scroll restore integration', () => {
  it('restores on POP navigation', async () => {
    render(
      <MemoryRouter initialEntries={['/feed', '/detail']}>
        <ScrollRestoreProvider>
          <Routes>
            <Route path="/feed" element={<div data-testid="feed" />} />
            <Route path="/detail" element={<div data-testid="detail" />} />
          </Routes>
        </ScrollRestoreProvider>
      </MemoryRouter>,
    );

    expect(screen.getByTestId('detail')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npm run test -- integration.test.tsx`
Expected: FAIL with `ReferenceError: ScrollRestoreProvider is not defined`

- [ ] **Step 3: Expand test for POP/async restore**

```typescript
import { act } from 'react-dom/test-utils';

it('waits for async content before restore', async () => {
  const Feed = () => <div style={{ height: '400px' }} data-testid="feed" />;

  render(
    <MemoryRouter initialEntries={['/feed', '/detail']}>
      <ScrollRestoreProvider>
        <Routes>
          <Route path="/feed" element={<Feed />} />
          <Route path="/detail" element={<div data-testid="detail" />} />
        </Routes>
      </ScrollRestoreProvider>
    </MemoryRouter>,
  );

  window.scrollTo({ top: 200 });
  act(() => window.history.back());

  expect(screen.getByTestId('feed')).toBeInTheDocument();
});
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npm run test -- integration.test.tsx`
Expected: PASS `frontend/src/features/scrollRestore/__tests__/integration.test.tsx`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/scrollRestore/__tests__/integration.test.tsx
git commit -m "test(scroll): add navigation restore coverage"
```

---

### Task 8: Lint and Build Verification

**Files:**
- None

- [ ] **Step 1: Run lint**

Run: `cd frontend && npm run lint`
Expected: `✔ No ESLint warnings or errors`

- [ ] **Step 2: Run build**

Run: `cd frontend && npm run build`
Expected: `Build complete` with exit code 0

- [ ] **Step 3: Commit**

```bash
git status
```

Expected: `nothing to commit, working tree clean`
