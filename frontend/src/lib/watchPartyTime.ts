export function formatPlaybackMs(ms: number): string {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000))
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }
  return `${minutes}:${String(seconds).padStart(2, '0')}`
}

export function expectedPlaybackMs(state: {
  playing: boolean
  position_ms: number
  updated_at: string
}): number {
  if (!state.playing) {
    return state.position_ms
  }
  const updatedAt = Date.parse(state.updated_at)
  if (!Number.isFinite(updatedAt)) {
    return state.position_ms
  }
  return state.position_ms + Math.max(0, Date.now() - updatedAt)
}
