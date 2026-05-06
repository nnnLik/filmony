# Feed UI Card Design

## Goal

Реализовать единый UX карточки в ленте с превью комментариев и возможностью оставить комментарий без ухода с главной, опираясь на новый контракт API ленты.

## API контракт

- **Эндпоинт:** `GET /api/cards/feed`
- **Авторизация:** текущая сессия (как остальные защищённые маршруты).
- **Query:** `cursor` — строковый идентификатор следующей страницы (id последней показанной карточки в предыдущем ответе); `limit` — по умолчанию 20, максимум 50.
- **Ответ (`MovieCardFeedPageResponse`):** `items`, `next_cursor`.
- **Элемент списка (`MovieCardFeedItemResponse`):**
  - Все поля как у детальной карточки: `user_id`, `film_*`, `rating`, `company`, `mood_before`, `mood_after`, `custom_tags`.
  - `card_author` — автор карточки (как автор комментария: `MovieCardCommentAuthorResponse`).
  - `comments_count` — число всех комментариев карточки (включая ответы).
  - `comments_preview` — не более **трёх** последних комментариев по времени добавления (`id`): отсортированы по возрастанию `id` в ответе; поля счётчиков ответов в превью равны 0.

Клиентское обёртывание: `getMovieCardFeedPage()` в [`frontend/src/api/cardApi.ts`](../../frontend/src/api/cardApi.ts), тип [`FeedMovieCard`](../../frontend/src/api/profileTypes.ts).

## Frontend

- **[`frontend/src/pages/FeedPage.tsx`](../../frontend/src/pages/FeedPage.tsx):** загрузка первой страницы, обработка пустых/ошибочных состояний, подгрузка по `next_cursor`, список карточек.
- **[`frontend/src/components/feed/FeedCard.tsx`](../../frontend/src/components/feed/FeedCard.tsx):** постер, название и год, оценка автора с подписью `card_author`, системные атрибуты досуга как компактные чипы (не простой текстовый список), пользовательские теги ограничены двумя видимыми и индексом `+N`, превью комментариев, текст «Комментариев: …», кнопка «Комментировать» раскрывает поле отправки через существующий `createMovieCardComment`, переход «Все комментарии» на `/cards/:id`. После успешной отправки только соответствующая карточка в состоянии обновляется.
- **[`frontend/src/components/feed/FeedCardSkeleton.tsx`](../../frontend/src/components/feed/FeedCardSkeleton.tsx):** состояние загрузки одиночной карточки.

## Success Criteria (соответствие)

- Карточка одним взглядом сообщает фильм и автора рейтинга.
- Системные признаки (компания, настроения) визуально отличны от текстового спама.
- Кастомные теги не раздувают layout (лимит 2 и `+N`).
- Комментирование из ленты без полной перезагрузки страницы; скролл не сбрасывается методом программирования состояния.
- Горизонтальный скролл ограничен (`max-width` / `overflow-x` на главном контенте страницы).

## Verification

Из корня репозитория (Docker для backend см. Makefile):

```bash
make backend-test-one target=src/tests/api/test_cards_routes.py::test_movie_card_feed_requires_auth
make backend-test-one target=src/tests/api/test_cards_routes.py::test_movie_card_feed_includes_comments_count_and_preview
make backend-test-one target=src/tests/api/test_cards_routes.py::test_movie_card_feed_cursor_pagination
cd frontend && npm run lint
```
