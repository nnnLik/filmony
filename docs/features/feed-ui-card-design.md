# Feed UI Card Design

## Goal

Реализовать единый UX карточки в ленте: компактное превью комментариев в ответе API, при раскрытии — полный список в прокручиваемой зоне и быстрый комментарий без ухода с главной.

## API контракт

- **Эндпоинт:** `GET /api/cards/feed`
- **Авторизация:** текущая сессия (как остальные защищённые маршруты).
- **Query:** `cursor` — строковый идентификатор следующей страницы (id последней показанной карточки в предыдущем ответе); `limit` — по умолчанию 20, максимум 50.
- **Ответ (`MovieCardFeedPageResponse`):** `items`, `next_cursor`.
- **Элемент списка (`MovieCardFeedItemResponse`):**
  - Все поля как у детальной карточки: `user_id`, `film_*`, `rating`, `company`, `mood_before`, `mood_after`, `custom_tags`, при наличии — `is_favorite` (любимое автора карточки).
  - `card_author` — автор карточки (как автор комментария: `MovieCardCommentAuthorResponse`).
  - `comments_count` — число всех комментариев карточки (включая ответы).
  - `comments_preview` — не более **трёх** последних комментариев по времени добавления (`id`): отсортированы по возрастанию `id` в ответе; поля счётчиков ответов в превью равны 0. Это **компактное превью для ответа ленты** (и локальное обновление после отправки комментария из ленты); **полный список** в UI ленты при раскрытии блока под карточкой строится отдельным запросом `GET /api/cards/{id}/comments` (с догрузкой по `next_cursor`), см. `listAllMovieCardComments()` в [`frontend/src/api/cardApi.ts`](../../frontend/src/api/cardApi.ts).

Клиентское обёртывание: `getMovieCardFeedPage()` в [`frontend/src/api/cardApi.ts`](../../frontend/src/api/cardApi.ts), тип [`FeedMovieCard`](../../frontend/src/api/profileTypes.ts).

## Frontend

- **[`frontend/src/pages/FeedPage.tsx`](../../frontend/src/pages/FeedPage.tsx):** загрузка первой страницы, обработка пустых/ошибочных состояний, подгрузка по `next_cursor`, список карточек.
- **[`frontend/src/components/feed/FeedCard.tsx`](../../frontend/src/components/feed/FeedCard.tsx):** постер, название и год, оценка автора с подписью `card_author`, системные атрибуты досуга как компактные чипы (не простой текстовый список), пользовательские теги ограничены двумя видимыми и индексом `+N`, строка «Комментарии» и счётчик, **стрелка раскрывает** блок: список **всех** комментариев в **прокручиваемой** зоне фиксированной высоты + быстрый ввод через `createMovieCardComment`; ссылки «Ответить» / превью родителя ведут на `/cards/:id` для полного треда. Счётчик и `comments_preview` в состоянии ленты по-прежнему обновляются локально после отправки. Если у карточки `is_favorite` (любимое **автора**), на постере включается нелитеральный визуальный акцент (см. раздел ниже). Вспомогательно: [`feedCardUtils.ts`](../../frontend/src/components/feed/feedCardUtils.ts), [`FeedCardIcons.tsx`](../../frontend/src/components/feed/FeedCardIcons.tsx), [`FeedAuthorFavoritePosterChrome.tsx`](../../frontend/src/components/feed/FeedAuthorFavoritePosterChrome.tsx).
- **[`frontend/src/components/feed/FeedCardSkeleton.tsx`](../../frontend/src/components/feed/FeedCardSkeleton.tsx):** состояние загрузки одиночной карточки.

## Success Criteria (соответствие)

- Карточка одним взглядом сообщает фильм и автора рейтинга.
- Системные признаки (компания, настроения) визуально отличны от текстового спама.
- Кастомные теги не раздувают layout (лимит 2 и `+N`).
- Комментирование из ленты без полной перезагрузки страницы; скролл не сбрасывается методом программирования состояния.
- Горизонтальный скролл ограничен (`max-width` / `overflow-x` на главном контенте страницы).

## Любимое автора на постере (`is_favorite`)

- **Цель:** визуально отличить карточку, которую автор отметил как любимую, **без** подписи «любимое» и **без** сердечка в чужой ленте (сердце у владельца остаётся для управления избранным).
- **Реализация:** слой [`FeedAuthorFavoritePosterChrome.tsx`](../../frontend/src/components/feed/FeedAuthorFavoritePosterChrome.tsx) — виньетка, внутреннее свечение в mint-тонах бренда, лёгкий grain, угловые скобы «видоискатель», усиленное кольцо/тень у блока постера; для скринридеров — нейтральный `sr-only` («Карточка отмечена автором»).
- **Продукт и рекомендации:** см. [`feed-author-favorite-signal.md`](feed-author-favorite-signal.md).

## Verification

Из корня репозитория (Docker для backend см. Makefile):

```bash
make backend-test-one target=src/tests/api/test_cards_routes.py::test_movie_card_feed_requires_auth
make backend-test-one target=src/tests/api/test_cards_routes.py::test_movie_card_feed_includes_comments_count_and_preview
make backend-test-one target=src/tests/api/test_cards_routes.py::test_movie_card_feed_cursor_pagination
cd frontend && npm run lint
```
