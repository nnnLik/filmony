import { describe, expect, it } from 'vitest'

import type { FeedPageItem } from '../../api/feedListPageTypes'
import { collectFeedPrimaryAuthorIds } from '../feedVisibleAuthorIds'

const VIEWER_ID = 'viewer-1'
const OTHER_ID = 'other-2'
const SOURCE_AUTHOR_ID = 'source-3'

function feedAuthor(userId: string, firstName: string) {
  return {
    id: userId,
    profile_slug: `user-${userId}`,
    username: null,
    first_name: firstName,
    last_name: null,
    display_name: null,
    photo_url: null,
  }
}

function movieCard(userId: string, id = 1): FeedPageItem {
  return {
    kind: 'movie_card',
    id,
    user_id: userId,
    feed_source: 'global',
    card_author: feedAuthor(userId, 'A'),
    comments_count: 0,
    comments_preview: [],
  } as unknown as FeedPageItem
}

function feedPost(
  userId: string,
  options?: { sourceCommentAuthorId?: string; id?: number },
): FeedPageItem {
  const sourceAuthorId = options?.sourceCommentAuthorId
  return {
    kind: 'feed_post',
    id: options?.id ?? 10,
    user_id: userId,
    author: feedAuthor(userId, 'B'),
    body: 'hello',
    image_url: null,
    referenced_movie_card_id: null,
    source_comment_id: sourceAuthorId != null ? 99 : null,
    created_at: '2026-01-01T00:00:00Z',
    feed_source: 'global',
    referenced_card: null,
    comments_count: 0,
    comments_preview: [],
    source_comment:
      sourceAuthorId != null
        ? {
            id: 99,
            text: 'quoted',
            image_url: null,
            author: feedAuthor(sourceAuthorId, 'C'),
            referenced_movie_cards: [],
            referenced_mentions: [],
          }
        : undefined,
  }
}

describe('collectFeedPrimaryAuthorIds', () => {
  it('returns empty arrays for empty feed', () => {
    expect(collectFeedPrimaryAuthorIds([], VIEWER_ID)).toEqual({
      tasteQuizOwnerIds: [],
      streakUserIds: [],
    })
  })

  it('includes movie card author in streaks and taste quiz when not viewer', () => {
    const result = collectFeedPrimaryAuthorIds([movieCard(OTHER_ID)], VIEWER_ID)
    expect(result.streakUserIds).toEqual([OTHER_ID])
    expect(result.tasteQuizOwnerIds).toEqual([OTHER_ID])
  })

  it('excludes own movie card author from taste quiz but keeps streak', () => {
    const result = collectFeedPrimaryAuthorIds([movieCard(VIEWER_ID)], VIEWER_ID)
    expect(result.streakUserIds).toEqual([VIEWER_ID])
    expect(result.tasteQuizOwnerIds).toEqual([])
  })

  it('includes feed post author and source comment author in streaks', () => {
    const result = collectFeedPrimaryAuthorIds(
      [feedPost(OTHER_ID, { sourceCommentAuthorId: SOURCE_AUTHOR_ID })],
      VIEWER_ID,
    )
    expect(result.streakUserIds).toEqual([OTHER_ID, SOURCE_AUTHOR_ID])
    expect(result.tasteQuizOwnerIds).toEqual([OTHER_ID, SOURCE_AUTHOR_ID])
  })

  it('excludes viewer from taste quiz for own post and own source quote', () => {
    const result = collectFeedPrimaryAuthorIds(
      [feedPost(VIEWER_ID, { sourceCommentAuthorId: VIEWER_ID })],
      VIEWER_ID,
    )
    expect(result.streakUserIds).toEqual([VIEWER_ID])
    expect(result.tasteQuizOwnerIds).toEqual([])
  })

  it('dedupes ids across items and filters empty strings', () => {
    const items: FeedPageItem[] = [
      movieCard(OTHER_ID, 1),
      movieCard(OTHER_ID, 2),
      feedPost(OTHER_ID, { id: 3 }),
      movieCard('  ', 4),
    ]
    const result = collectFeedPrimaryAuthorIds(items, null)
    expect(result.streakUserIds).toEqual([OTHER_ID])
    expect(result.tasteQuizOwnerIds).toEqual([OTHER_ID])
  })
})
