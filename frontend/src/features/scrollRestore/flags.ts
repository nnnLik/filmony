export const scrollRestoreConfig = {
  ttlMs: 1_800_000,
  maxEntries: 50,
  sampleRate: 0.1,
};

export function isScrollRestoreEnabled(): boolean {
  return Boolean((window as Window & { __flags__?: Record<string, boolean> }).__flags__?.scrollRestore);
}
