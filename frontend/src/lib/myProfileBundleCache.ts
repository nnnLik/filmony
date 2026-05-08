import type { MovieCardPage, MyProfile } from '../api/profileTypes'

import { MY_PROFILE_BUNDLE_STORAGE_KEY, MY_PROFILE_CACHE_MAX_AGE_MS } from './filmonySession'

/** Событие на `window`: профиль в sessionStorage обновился или очищен */
export const MY_PROFILE_BUNDLE_CHANGED_EVENT = 'filmony-my-profile-bundle-changed'

function notifyMyProfileBundleChanged(): void {
  try {
    window.dispatchEvent(new CustomEvent(MY_PROFILE_BUNDLE_CHANGED_EVENT))
  } catch {
    /* ignore */
  }
}

export type MyProfileBundle = {
  profile: MyProfile
  cards: MovieCardPage | null
  storedAt: number
}

export function readMyProfileBundleCache(): MyProfileBundle | null {
  try {
    const raw = sessionStorage.getItem(MY_PROFILE_BUNDLE_STORAGE_KEY)
    if (raw == null || raw === '') {
      return null
    }
    const parsed = JSON.parse(raw) as MyProfileBundle
    if (
      parsed == null ||
      typeof parsed.storedAt !== 'number' ||
      parsed.profile == null ||
      typeof parsed.profile.id !== 'string'
    ) {
      return null
    }
    if (Date.now() - parsed.storedAt > MY_PROFILE_CACHE_MAX_AGE_MS) {
      sessionStorage.removeItem(MY_PROFILE_BUNDLE_STORAGE_KEY)
      return null
    }
    parsed.profile = {
      ...parsed.profile,
      followers_count: parsed.profile.followers_count ?? 0,
      following_count: parsed.profile.following_count ?? 0,
      watchlist_count: parsed.profile.watchlist_count ?? 0,
      favorites_count: parsed.profile.favorites_count ?? 0,
    }
    return parsed
  } catch {
    try {
      sessionStorage.removeItem(MY_PROFILE_BUNDLE_STORAGE_KEY)
    } catch {
      /* ignore */
    }
    return null
  }
}

export function writeMyProfileBundleCache(profile: MyProfile, cards: MovieCardPage | null): void {
  try {
    const payload: MyProfileBundle = {
      profile,
      cards,
      storedAt: Date.now(),
    }
    sessionStorage.setItem(MY_PROFILE_BUNDLE_STORAGE_KEY, JSON.stringify(payload))
    notifyMyProfileBundleChanged()
  } catch {
    /* ignore */
  }
}

export function clearMyProfileBundleCache(): void {
  try {
    sessionStorage.removeItem(MY_PROFILE_BUNDLE_STORAGE_KEY)
    notifyMyProfileBundleChanged()
  } catch {
    /* ignore */
  }
}
