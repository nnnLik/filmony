export type ScrollRestoreEntry = {
  position: number;
  containerId: string | null;
  updatedAt: number;
};

type StorageOptions = {
  ttlMs: number;
  maxEntries: number;
};

type HydrateOptions = StorageOptions & {
  storageKey: string;
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
