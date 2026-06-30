import { describe, expect, it, vi } from 'vitest';

import { ScrollRestoreStorage } from '../storage';

describe('ScrollRestoreStorage', () => {
  it('evicts entries beyond the cap', () => {
    const now = 10_000;
    vi.spyOn(Date, 'now').mockReturnValue(now);
    const storage = new ScrollRestoreStorage({ ttlMs: 1_800_000, maxEntries: 2 });
    storage.set('a', { position: 10, containerId: null, updatedAt: 1 });
    storage.set('b', { position: 20, containerId: null, updatedAt: 2 });
    storage.set('c', { position: 30, containerId: null, updatedAt: 3 });

    expect(storage.get('a')).toBeNull();
    expect(storage.get('b')?.position).toBe(20);
    vi.restoreAllMocks();
  });

  it('expires entries older than ttl', () => {
    const now = 10_000;
    vi.spyOn(Date, 'now').mockReturnValue(now);
    const storage = new ScrollRestoreStorage({ ttlMs: 500, maxEntries: 50 });
    storage.set('feed', { position: 150, containerId: null, updatedAt: now - 600 });

    expect(storage.get('feed')).toBeNull();
    vi.restoreAllMocks();
  });
});
