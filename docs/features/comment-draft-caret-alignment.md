# Выравнивание курсора в черновиках комментариев и постов

## Проблема
Поля `CommentDraftSingleLineInput` и `CommentDraftMultiline` рисуют rich-зеркало (`CommentBodyWithReactionTokens`: картинки реакций, чипы `@mention`) поверх прозрачного нативного поля. Ширина вёрстки зеркала не совпадает с метриками **сырой** строки `value` в `input`/`textarea`, из-за чего нативный курсор визуально «уезжает» (эмодзи, вставленные реакции).

## Решение
1. Зеркало снова рендерит `CommentBodyWithReactionTokens` с флагом **`annotateCharRanges`**: на каждый сегмент вешаются `data-segment`, `data-char-start`, `data-char-end` (полуинтервал в UTF-16 в исходной строке).
2. Нативный курсор скрыт (`caret-transparent`), поверх поля рисуется **фейковый курсор** (`span` 1px), позиция считается через `Range` + `getBoundingClientRect()` относительно обёртки (`richMirrorCaretPositionInRoot` в `frontend/src/lib/commentDraftCaretGeometry.ts`).
3. Типографика и переносы у `textarea` согласованы с зеркалом (`break-words`, `whitespace-pre-wrap`, `leading-normal`).

## Технические детали
- `frontend/src/components/comments/CommentDraftMirrorField.tsx` — зеркало, измерение, overlay-курсор, `ResizeObserver` и `selectionchange`.
- `frontend/src/components/comments/CommentBodyWithReactionTokens.tsx` — опциональная разметка диапазонов для черновика; при `annotateCharRanges` не показывается префикс ошибки каталога (чтобы не ломать соответствие DOM и `value`).
- `frontend/src/lib/commentReactionTokens.ts` — `splitCommentTextIntoSegmentsWithRanges`, общая логика с `splitCommentTextIntoSegments`.
- `frontend/src/lib/commentDraftCaretGeometry.ts` — геометрия курсора.

## Ограничения
- Внутри одного токена реакции/упоминания курсор визуально привязан к середине токена (до/после чипа), а не к каждому символу `⟦…⟧`.
- Выделение текста по-прежнему подсвечивается нативным `::selection` по **прозрачной** строке и может не совпадать по ширине с rich-зеркалом при смешанном контенте.

## Проверка
```bash
cd frontend && npm run lint && npm run build
```
