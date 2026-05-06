import type { PublicProfile } from '../api/profileTypes'

export function profileInitials(
  p: Pick<PublicProfile, 'display_name' | 'first_name' | 'username'>,
): string {
  const base =
    p.display_name?.trim() || [p.first_name, p.username].filter(Boolean).join(' ') || '?'
  const parts = base.split(/\s+/).filter(Boolean)
  if (parts.length >= 2) {
    return (parts[0].slice(0, 1) + parts[1].slice(0, 1)).toUpperCase()
  }
  return base.slice(0, 2).toUpperCase()
}

export function displayNameFromProfile(
  p: Pick<PublicProfile, 'display_name' | 'first_name' | 'last_name' | 'username'>,
): string {
  if (p.display_name?.trim()) {
    return p.display_name.trim()
  }
  const n = [p.first_name, p.last_name].filter(Boolean).join(' ')
  if (n) {
    return n
  }
  if (p.username) {
    return `@${p.username}`
  }
  return 'Пользователь'
}
