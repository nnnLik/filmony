import { useContext } from 'react'

import {
  FeedCardGlobalAudioContext,
  type FeedCardGlobalAudioContextValue,
} from '../context/feedCardGlobalAudioContext'

export function useFeedCardGlobalAudio(): FeedCardGlobalAudioContextValue {
  const v = useContext(FeedCardGlobalAudioContext)
  if (v == null) {
    throw new Error('useFeedCardGlobalAudio must be used within FeedCardGlobalAudioProvider')
  }
  return v
}

/** For UI (FAB) outside feed cards: no-op when the provider is absent. */
export function useOptionalFeedCardGlobalAudio(): FeedCardGlobalAudioContextValue | null {
  return useContext(FeedCardGlobalAudioContext)
}
