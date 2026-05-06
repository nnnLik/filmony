import type { ReactionActor } from '../../../api/profileTypes'

export function displayActorName(a: ReactionActor): string {
  if (a.display_name && a.display_name.trim() !== '') return a.display_name.trim()
  const u = (a.username ?? '').trim()
  if (u !== '') return `@${u}`
  const parts = [a.first_name, a.last_name].filter(Boolean).join(' ').trim()
  if (parts !== '') return parts
  return a.profile_slug
}
