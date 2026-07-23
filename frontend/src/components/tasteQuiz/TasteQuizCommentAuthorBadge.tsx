import type { TasteQuizKnowledgeBatchItem } from '../../api/tasteQuizTypes'
import { TasteQuizKnowledgeBadge } from './TasteQuizKnowledgeBadge'

export type TasteQuizCommentAuthorBadgeProps = {
  knowledgeByAuthor: Record<string, TasteQuizKnowledgeBatchItem>
  authorId: string
}

export function TasteQuizCommentAuthorBadge({
  knowledgeByAuthor,
  authorId,
}: TasteQuizCommentAuthorBadgeProps) {
  const item = knowledgeByAuthor[authorId]
  if (item == null || item.attempts <= 0) {
    return null
  }
  return <TasteQuizKnowledgeBadge item={item} />
}
