import type { FeedPageItem } from '../api/feedListPageTypes'

function isNonEmptyUserId(id: string | null | undefined): id is string {
  return id != null && id.trim() !== ''
}

function dedupeUserIds(ids: Iterable<string>): string[] {
  return [...new Set([...ids].filter(isNonEmptyUserId))].sort()
}

function isViewer(viewerUserId: string | null, userId: string): boolean {
  return viewerUserId != null && viewerUserId !== '' && viewerUserId === userId
}

/**
 * Collects primary (page-visible) author ids for batch streak / taste-quiz badge queries.
 * Comment authors from expanded panels are registered separately via FeedAuthorBadgesProvider.
 */
export function collectFeedPrimaryAuthorIds(
  items: FeedPageItem[],
  viewerUserId: string | null,
): { tasteQuizOwnerIds: string[]; streakUserIds: string[] } {
  const tasteQuizOwnerIds = new Set<string>()
  const streakUserIds = new Set<string>()

  for (const item of items) {
    if (item.kind === 'feed_post') {
      const isOwnPost = isViewer(viewerUserId, item.user_id)

      if (isNonEmptyUserId(item.user_id)) {
        streakUserIds.add(item.user_id)
        if (!isOwnPost && !isViewer(viewerUserId, item.user_id)) {
          tasteQuizOwnerIds.add(item.user_id)
        }
      }

      const sourceAuthorId = item.source_comment?.author.id
      if (isNonEmptyUserId(sourceAuthorId)) {
        streakUserIds.add(sourceAuthorId)
        if (!isViewer(viewerUserId, sourceAuthorId)) {
          tasteQuizOwnerIds.add(sourceAuthorId)
        }
      }
    } else {
      const isOwnCard = isViewer(viewerUserId, item.user_id)

      if (isNonEmptyUserId(item.user_id)) {
        streakUserIds.add(item.user_id)
        if (!isOwnCard && !isViewer(viewerUserId, item.user_id)) {
          tasteQuizOwnerIds.add(item.user_id)
        }
      }
    }
  }

  return {
    tasteQuizOwnerIds: dedupeUserIds(tasteQuizOwnerIds),
    streakUserIds: dedupeUserIds(streakUserIds),
  }
}
