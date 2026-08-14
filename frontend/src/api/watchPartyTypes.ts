export type WatchPartyPlaybackState = {
  playing: boolean
  position_ms: number
  updated_at: string
  host_user_id: string
  version: number
}

export type WatchPartyMember = {
  user_id: string
  display_name: string
  photo_url: string | null
  role: 'host' | 'guest'
  status: 'active' | 'away' | 'left'
  joined_at: string
  position_ms?: number | null
  position_playing?: boolean | null
  position_at?: string | null
}

export type WatchPartyMessage = {
  id: number
  author_user_id: string
  body: string
  created_at: string
}

export type WatchPartySnapshot = {
  id: string
  invite_slug: string
  invite_url: string
  status: string
  film_id: number
  film_title: string
  film_poster_url: string | null
  playback_iframe_url: string
  playback_expires_at: string
  playback_state: WatchPartyPlaybackState
  host_user_id: string
  members: WatchPartyMember[]
  viewer_role: 'host' | 'guest' | null
  viewer_status: string | null
}

export type WatchPartyCreateResponse = {
  id: string
  invite_slug: string
  invite_url: string
}

export type WatchPartySlugResolve = {
  party_id: string
  invite_slug: string
  status: string
}

export type ActivePartyConflictDetail = {
  code: 'already_in_active_party'
  active_party_id: string
  invite_slug: string
}

export type WatchPartySseEvent = {
  seq: number
  type:
    | 'snapshot'
    | 'playback_state'
    | 'chat_message'
    | 'chat_message_deleted'
    | 'presence'
    | 'member_position'
    | 'party_ended'
    | 'ping'
    | 'typing'
  payload: Record<string, unknown>
}

export type WatchingNowBatchItem = {
  film_id: number
  film_title: string
  party_id?: string
}

export const WATCHING_NOW_BATCH_MAX_USER_IDS = 100

export type WatchingNowBatchResponse = {
  items: Record<string, WatchingNowBatchItem>
}

export type FollowingWatchingNowItem = {
  user_id: string
  display_name: string
  photo_url: string | null
  slug: string
  film_id: number
  film_title: string
  film_poster_url: string | null
  invite_slug: string | null
  party_id: string | null
}

export type FollowingWatchingNowResponse = {
  items: FollowingWatchingNowItem[]
}

export type WatchPartyBridgeResponse = {
  watch_session_id: string
}

export type WatchPartySnapshotPayload = {
  party_id: string
  status: string
  playback_state: WatchPartyPlaybackState
  members: WatchPartyMember[]
  messages: WatchPartyMessage[]
}
