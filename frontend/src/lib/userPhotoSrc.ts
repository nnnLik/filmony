import { resolveApiUrl } from '../api/client'

const CUSTOM_AVATAR_PATH = '/api/users/avatar-media/user_media/avatars/'

/** Absolute Telegram URLs stay as-is. Our media paths pick up `VITE_API_ORIGIN`. */
export function userPhotoSrc(photoUrl: string | null | undefined): string | undefined {
  if (photoUrl == null) {
    return undefined
  }
  const trimmed = photoUrl.trim()
  if (trimmed === '') {
    return undefined
  }
  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
    return trimmed
  }
  return resolveApiUrl(trimmed.startsWith('/') ? trimmed : `/${trimmed}`)
}

export function isCustomAvatarPhotoUrl(photoUrl: string | null | undefined): boolean {
  if (photoUrl == null) {
    return false
  }
  const path = photoUrl.trim().split('?', 1)[0]
  return path.includes(CUSTOM_AVATAR_PATH)
}
