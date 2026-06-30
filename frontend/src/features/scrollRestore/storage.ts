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
