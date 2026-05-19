import { createContext, type RefObject } from 'react'

export type FeedCardGlobalAudioContextValue = {
  /** Master switch: when false, playback is paused and new plays are blocked until re-enabled from a card or FAB. */
  enabled: boolean
  setFeedAudioEnabled: (next: boolean) => void
  toggleFeedAudioEnabled: () => void
  playingCardId: number | null
  /** True when the shared element is paused (or no track). */
  paused: boolean
  audioRef: RefObject<HTMLAudioElement | null>
  toggleCardAudio: (cardId: number, audioUrlRaw: string) => void
}

export const FeedCardGlobalAudioContext = createContext<FeedCardGlobalAudioContextValue | null>(null)
