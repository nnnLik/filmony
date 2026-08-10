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

export function expectedPlaybackMs(
  state: {
    playing: boolean
    position_ms: number
    updated_at: string
  },
  nowMs: number = Date.now(),
): number {
  if (!state.playing) {
    return state.position_ms
  }
  const updatedAt = Date.parse(state.updated_at)
  if (!Number.isFinite(updatedAt)) {
    return state.position_ms
  }
  return state.position_ms + Math.max(0, nowMs - updatedAt)
}

type MemberPositionSource = {
  user_id: string
  position_ms?: number | null
  position_playing?: boolean | null
  position_at?: string | null
}

export function memberDisplayPositionMs(
  member: MemberPositionSource,
  hostUserId: string,
  hostPlaybackState: {
    playing: boolean
    position_ms: number
    updated_at: string
  },
  nowMs: number = Date.now(),
): number | null {
  if (member.user_id === hostUserId) {
    if (!hostPlaybackState.playing) {
      return hostPlaybackState.position_ms
    }
    const updatedAt = Date.parse(hostPlaybackState.updated_at)
    if (!Number.isFinite(updatedAt)) {
      return hostPlaybackState.position_ms
    }
    return hostPlaybackState.position_ms + Math.max(0, nowMs - updatedAt)
  }
  if (member.position_ms == null || member.position_at == null) {
    return null
  }
  if (!member.position_playing) {
    return member.position_ms
  }
  const updatedAt = Date.parse(member.position_at)
  if (!Number.isFinite(updatedAt)) {
    return member.position_ms
  }
  return member.position_ms + Math.max(0, nowMs - updatedAt)
}

export function memberPositionDeltaSeconds(
  memberMs: number | null,
  hostMs: number | null,
): number | null {
  if (memberMs == null || hostMs == null) {
    return null
  }
  return Math.round((memberMs - hostMs) / 1000)
}
