- Timestamp: 2026-05-06 22:30 UTC
- Feature slug: `feed-ui-card-design`
- Action type: `code`

## Summary
Реализован backend `GET /api/cards/feed` с подсчётом комментариев и превью до двух последних, сервис `ListMovieCardFeedService`, ответ включает `card_author`; на frontend добавлены типы/API, компоненты `FeedCard` / `FeedCardSkeleton` и загрузка ленты на `FeedPage` с локальным обновлением превью и счётчика после отправки комментария.

## Files
- `backend/src/services/cards/list_movie_card_feed.py`
- `backend/src/api/cards/schemas.py`
- `backend/src/api/cards/routes.py`
- `frontend/src/api/profileTypes.ts`
- `frontend/src/api/cardApi.ts`
- `frontend/src/components/feed/FeedCard.tsx`
- `frontend/src/components/feed/FeedCardSkeleton.tsx`
- `frontend/src/pages/FeedPage.tsx`

## Verification
- Локально в этой сессии не запускалось (нет доступа к Docker/shell по политике окружения). Рекомендуется в Docker:  
  `make backend-test-one target=src/tests/api/test_cards_routes.py::test_movie_card_feed_requires_auth`  
  и полнее: `make backend-test-one target=src/tests/api/test_cards_routes.py`  
  фронт: `cd frontend && npm run lint`.
