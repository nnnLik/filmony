# Plan: comment-draft-caret-alignment

1. Подтвердить причину: зеркало рендерило `CommentBodyWithReactionTokens` (img, чипы), ширина отличалась от строки в нативном поле.
2. Заменить зеркало на plain text того же `value`; выровнять классы textarea с зеркалом.
3. Прогнать `npm run lint` и `npm run build` в `frontend/`.
4. Оформить `result.md`, `docs/features/…`, запись в action log.
