import type { WatchPartyMessage } from '../api/watchPartyTypes'

/** Upsert messages by id and return stable ascending sort by id. */
export function mergeWatchPartyMessages(
  existing: readonly WatchPartyMessage[],
  incoming: readonly WatchPartyMessage[],
): WatchPartyMessage[] {
  const byId = new Map<number, WatchPartyMessage>()
  for (const message of existing) {
    byId.set(message.id, message)
  }
  for (const message of incoming) {
    byId.set(message.id, message)
  }
  return [...byId.values()].sort((a, b) => a.id - b.id)
}
