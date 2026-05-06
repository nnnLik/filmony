# Feature: movie-card-comments-telegram-like

## Что реализовано
- Комментарии карточки фильма переведены с древовидного рендера на плоский Telegram-like сценарий.
- `GET /api/cards/{card_id}/comments` теперь возвращает плоский список всех комментариев карточки (включая ответы) с cursor pagination.
- `parent_comment_id` остался базовой связью "ответ на сообщение" для создания и отображения reply.
- В UI комментарий-ответ получил компактный reply-preview родительского сообщения.
- По нажатию на reply-preview интерфейс:
  - находит родителя в загруженном списке, или
  - автоматически догружает страницы `GET /comments` до нахождения родителя/исчерпания списка,
  - прокручивает к родителю и подсвечивает его.
- Удален отдельный экран thread и роут `/cards/:cardId/comments/:commentId/thread`.

## Контракт API после изменения
- `GET /api/cards/{card_id}/comments?cursor=&limit=`
  - Возвращает плоский список комментариев карточки по возрастанию `id` (старые в начале).
  - В каждом элементе сохраняются поля:
    - `id`, `movie_card_id`, `parent_comment_id`, `text`, `created_at`
    - `replies_count`, `total_descendants_count`
    - `author`
  - Пагинация: `next_cursor`.
- `GET /api/cards/{card_id}/comments/{comment_id}/replies`
  - Сохранен для совместимости.

## Основные изменения в коде
- Backend:
  - `backend/src/services/cards/list_movie_card_comments.py`
  - `backend/src/api/cards/routes.py`
  - `backend/src/tests/api/test_cards_routes.py`
- Frontend:
  - `frontend/src/pages/MovieCardDetailPage.tsx`
  - `frontend/src/routes.tsx`
  - `frontend/src/pages/MovieCardCommentThreadPage.tsx` (удален)

## Проверка
- Выполнено:
  - `ReadLints` по измененным backend/frontend файлам: ошибок нет.
- В этой сессии shell-команды не выполнены (инструмент вернул `Rejected: User chose to skip`), поэтому запуск команд нужно подтвердить локально:
  - `make backend-test-one target=src/tests/api/test_cards_routes.py`
  - `make backend-test`
  - `cd frontend && npm run lint && npm run build`
