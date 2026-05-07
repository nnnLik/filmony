# Feature: movie-card-comments

## Что реализовано
- **Лента (`FeedCard`):** при раскрытии блока комментариев под карточкой клиент запрашивает полный плоский список через `GET /api/cards/{card_id}/comments` (с пагинацией до конца) и отображает его в области **ограниченной высоты с вертикальным скроллом**; поле быстрого комментария остаётся под списком. Поле `comments_preview` в ответе **`GET /api/cards/feed`** по-прежнему даёт только короткое превью для карточки в ленте.
- Backend API комментариев под карточкой фильма:
  - `POST /api/cards/{card_id}/comments`
  - `GET /api/cards/{card_id}/comments`
  - `GET /api/cards/{card_id}/comments/{comment_id}/replies`
- Поддержаны ответы любой глубины через `parent_comment_id`.
- Чтение комментариев и ответов сделано публичным.
- Создание комментариев/ответов доступно только авторизованным пользователям.
- UI карточки переведен на поуровневую загрузку ответов (`roots + replies`), исправлен баг «ответы не отображаются».
- Для длинных веток добавлен переход в отдельный экран:
  - на карточке при `total_descendants_count > 4` показывается `Показать остальные`;
  - роут ветки: `/cards/:cardId/comments/:commentId/thread`.

## Контракт
- `POST /api/cards/{card_id}/comments`
  - Body: `{ "text": string, "parent_comment_id": int | null }`
  - Ошибки:
    - `401` — нет сессии
    - `404` — карточка или parent не найдены
    - `422` — пустой/слишком длинный текст или parent принадлежит другой карточке
- `GET /api/cards/{card_id}/comments?cursor=&limit=`
  - Возвращает только корневые комментарии.
- `GET /api/cards/{card_id}/comments/{comment_id}/replies?cursor=&limit=`
  - Возвращает только дочерние ответы указанного комментария.

Оба `GET` отдают:
- `items[]` с полями комментария и автора;
- `replies_count` для каждого элемента;
- `total_descendants_count` для оценки размера всей ветки;
- `next_cursor` для постраничной загрузки.

## Основные изменения в коде
- Модель/миграции:
  - `backend/src/models/movie_card_comment.py`
  - `backend/src/migrations/versions/c9d2e8a1b7c3_comment_branch_index.py`
- Сервисы:
  - `backend/src/services/cards/create_movie_card_comment.py`
  - `backend/src/services/cards/list_movie_card_comments.py`
- API:
  - `backend/src/api/cards/schemas.py`
  - `backend/src/api/cards/routes.py`
- Тесты:
  - `backend/src/tests/api/test_cards_routes.py`
- Frontend:
  - `frontend/src/api/cardApi.ts`
  - `frontend/src/api/profileTypes.ts`
  - `frontend/src/pages/MovieCardDetailPage.tsx`
  - `frontend/src/pages/MovieCardCommentThreadPage.tsx`
  - `frontend/src/routes.tsx`

## Проверка
- Выполнено: `ReadLints` по изменённым backend/frontend файлам, ошибок нет.
- Требуется ручной запуск в локальном окружении:
  - `make backend-test-one target=src/tests/api/test_cards_routes.py`
  - `make backend-test`
