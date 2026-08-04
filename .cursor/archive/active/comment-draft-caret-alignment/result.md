# Result: comment-draft-caret-alignment

## Status
`completed`

## Что сделано
- Зеркало черновика снова показывает реакции и @-упоминания через `CommentBodyWithReactionTokens` с разметкой диапазонов символов (`annotateCharRanges`).
- Нативный курсор скрыт; позиция курсора рисуется отдельным слоем по `Range` (`commentDraftCaretGeometry.ts`), чтобы совпадать с rich-вёрсткой.
- Добавлены `splitCommentTextIntoSegmentsWithRanges` и рефакторинг `splitCommentTextIntoSegments` в `commentReactionTokens.ts`.
- Синхронизация переносов/типографики multiline textarea с зеркалом сохранена.

## Изменённые файлы
- `frontend/src/components/comments/CommentDraftMirrorField.tsx`
- `frontend/src/components/comments/CommentBodyWithReactionTokens.tsx`
- `frontend/src/lib/commentReactionTokens.ts`
- `frontend/src/lib/commentDraftCaretGeometry.ts`

## Проверка
- `cd frontend && npm run lint && npm run build` — успешно.

## Ограничения
- Курсор внутри токена реакции/mention — только до/после чипа (середина токена как порог).
- Подсветка выделения (`::selection`) остаётся по прозрачному тексту и может расходиться с rich-слоем.

## Тесты
- Автотестов под визуальную геометрию нет.
