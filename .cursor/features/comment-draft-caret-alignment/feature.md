# Comment / post draft: caret alignment

## Scope
- Поля черновика комментария и многострочного текста (`CommentDraftSingleLineInput`, `CommentDraftMultiline`): курсор не должен визуально расходиться с текстом при вводе эмодзи и вставке токенов реакций / упоминаний.

## Acceptance criteria
- Rich-зеркало (`CommentBodyWithReactionTokens`) в черновиках; курсор визуально совпадает с набором (фейковый курсор по `Range` / `data-char-*`).
- `splitCommentTextIntoSegmentsWithRanges` для привязки DOM к UTF-16 индексам.
- `npm run lint` и `npm run build` в `frontend/` проходят.

## Out of scope
- Полная синхронизация визуального выделения текста с rich-зеркалом (остаётся нативный `::selection` по прозрачному `value`).
