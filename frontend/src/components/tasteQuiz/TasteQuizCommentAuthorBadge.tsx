import type { TasteQuizKnowledgeBatchItem } from '../../api/tasteQuizTypes'
import { TasteQuizKnowledgeBadge } from './TasteQuizKnowledgeBadge'

export type TasteQuizCommentAuthorBadgeProps = {
  /** Owner (comment author) id → viewer's knowledge stats; use `useTasteQuizKnowledgeOfUsers().knowledgeByOwnerId`. */
  knowledgeByAuthor: Record<string, TasteQuizKnowledgeBatchItem>
  authorId: string
  viewerId: string | null
}

export function TasteQuizCommentAuthorBadge({
  knowledgeByAuthor,
  authorId,
  viewerId,
}: TasteQuizCommentAuthorBadgeProps) {
  if (viewerId != null && viewerId === authorId) {
    return null
  }
  const item = knowledgeByAuthor[authorId]
  if (item == null || item.attempts <= 0) {
    return null
  }
  return <TasteQuizKnowledgeBadge item={item} />
}
