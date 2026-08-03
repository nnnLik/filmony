/** Format cache timestamp for offline feed banner (ru-RU). */
export function formatOfflineCacheTimestamp(storedAtMs: number): string {
  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(storedAtMs))
}
