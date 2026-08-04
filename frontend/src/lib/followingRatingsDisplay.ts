import type { FollowingRatingEntry } from '../api/profileTypes'
import { displayNameFromProfile, profileInitials } from './profileDisplay'

export type FollowingRatingRow = FollowingRatingEntry & {
  is_viewer?: boolean
}

export function followingRowShowsPlannedLabel(row: FollowingRatingRow): boolean {
  return row.is_planned === true || row.rating == null || row.rating < 1
}

export function buildFollowingRatingDisplayRows(
  viewerRating: FollowingRatingRow | null | undefined,
  items: FollowingRatingRow[],
): FollowingRatingRow[] {
  const rows: FollowingRatingRow[] = []
  if (viewerRating != null) {
    rows.push({ ...viewerRating, is_viewer: true })
  }
  for (const row of items) {
    rows.push({ ...row, is_viewer: false })
  }
  return rows
}

function followingRowToProfileFields(row: FollowingRatingRow) {
  return {
    display_name: row.display_name,
    first_name: row.first_name,
    last_name: row.last_name,
    username: row.username,
  }
}

export function followingRowDisplayName(row: FollowingRatingRow): string {
  if (row.is_viewer) return 'Вы'
  return displayNameFromProfile(followingRowToProfileFields(row))
}

export function followingRowInitials(row: FollowingRatingRow): string {
  if (row.is_viewer) return 'В'
  const profile = followingRowToProfileFields(row)
  return profileInitials({
    display_name: profile.display_name,
    first_name: profile.first_name,
    username: profile.username,
  })
}
