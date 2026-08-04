import type { RefObject } from 'react'

import type { FeedPostInFeed } from '../../api/feedInFeedTypes'
import { FeedPostCard } from '../feed/FeedPostCard'
import { ProfileTabSkeleton } from './ProfileTabSkeleton'
import { TabEmptyState } from '../ui/TabEmptyState'

type ProfilePostsPanelProps = {
  posts: { items: FeedPostInFeed[]; next_cursor: string | null } | null
  error: string | null
  loading: boolean
  isFetchingNextPage: boolean
  loadMoreRef: RefObject<HTMLDivElement | null>
  viewerUserId: string | null
  onPostDeleted: (postId: number) => void
  emptyUserId?: string | null
  className?: string
  listClassName?: string
  postKeyPrefix?: string
}

export function ProfilePostsPanel({
  posts,
  error,
  loading,
  isFetchingNextPage,
  loadMoreRef,
  viewerUserId,
  onPostDeleted,
  emptyUserId,
  className,
  listClassName = 'flex flex-col gap-3 px-1',
  postKeyPrefix = 'profile-post',
}: ProfilePostsPanelProps) {
  return (
    <div className={className}>
      {error != null ? (
        <p className="filmony-text-panel text-center text-sm text-(--tgui--destructive_text_color)">{error}</p>
      ) : null}
      {loading ? <ProfileTabSkeleton /> : null}
      {!loading && posts != null && posts.items.length === 0 ? (
        <TabEmptyState
          poolKey="profile_posts_empty"
          fallback="Пока нет постов в ленте"
          userId={emptyUserId ?? viewerUserId}
        />
      ) : null}
      {!loading && posts != null && posts.items.length > 0 ? (
        <div className={listClassName}>
          {posts.items.map((post) => (
            <FeedPostCard
              key={`${postKeyPrefix}-${post.id}`}
              post={post}
              viewerUserId={viewerUserId}
              onPostDeleted={onPostDeleted}
            />
          ))}
          {posts.next_cursor != null && posts.next_cursor !== '' ? (
            <>
              <div ref={loadMoreRef} className="h-1 w-full shrink-0" aria-hidden />
              {isFetchingNextPage ? (
                <p className="text-center text-xs text-(--tgui--hint_color)">Подгружаем посты…</p>
              ) : null}
            </>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
