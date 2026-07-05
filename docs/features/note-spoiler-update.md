# Заметки: лимит 1000 и спойлеры

## Лимит заметки
- Поле `watch_note` карточки: **до 1000 символов** (ранее 500).
- Константа backend: `backend/src/const/text_limits.py` → `WATCH_NOTE_MAX_LEN`.
- Frontend: `frontend/src/lib/watchNoteLimits.ts` → `MAX_WATCH_NOTE_LEN`.

## Формат спойлера
Текст хранится как plain string с inline-маркерами (как реакции и @mention):

```
⟦S⟧скрытый текст⟦/S⟧
```

- Backend проверяет баланс маркеров, запрещает вложенность и пустые блоки.
- В UI скрытый фрагмент показывается кнопкой «Спойлер · нажмите, чтобы показать».

## Как пометить спойлером (composer)
1. Выделите фрагмент текста.
2. Нажмите кнопку с иконкой **EyeOff** (подсказка «Спойлер») рядом с реакциями.
3. Повторное нажатие с тем же выделением **снимает** спойлер.
4. Без выделения вставляется шаблон `⟦S⟧спойлер⟦/S⟧` с курсором на placeholder.

## Где доступно
- Заметка карточки (создание / редактирование / watchlist note).
- Комментарии к карточкам и постам ленты.
- Тело поста (`FeedComposeSheet`).

## Технические файлы
- `backend/src/services/text/spoiler_tokens.py`
- `frontend/src/lib/spoilerTokens.ts`
- `frontend/src/components/comments/SpoilerRevealBlock.tsx`
- `frontend/src/components/comments/CommentSpoilerToggleButton.tsx`
- `frontend/src/components/comments/CommentBodyWithReactionTokens.tsx`

## Проверка
```bash
cd frontend && npm run lint && npm run build
npm run test -- src/lib/__tests__/spoilerTokens.test.ts
make backend-test-one target=src/tests/services/test_spoiler_tokens.py
```
