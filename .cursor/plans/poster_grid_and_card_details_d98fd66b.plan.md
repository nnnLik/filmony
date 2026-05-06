---
name: Poster grid and card details
overview: Сделать карточки в профилях едиными постерами без текста и добавить кликабельную детальную страницу карточки с полноценной загрузкой по URL, где часть блоков будет статическим mock по референсу.
todos:
  - id: backend-card-detail-endpoint
    content: Добавить backend endpoint `GET /api/cards/{card_id}` с проверкой доступа и схемой ответа для деталки
    status: completed
  - id: backend-tests-card-detail
    content: Покрыть новый endpoint тестами (happy path, 401, 404, доступ)
    status: completed
  - id: poster-grid-profile-pages
    content: Заменить списки карточек в `ProfilePage` и `PublicProfilePage` на одинаковую сетку постеров без текста
    status: completed
  - id: frontend-card-detail-page
    content: Добавить страницу деталки карточки по маршруту `/cards/:cardId` с загрузкой данных
    status: completed
  - id: mock-sections-in-detail
    content: Добавить статические mock-блоки на деталке по структуре макета
    status: completed
  - id: wire-routing-and-api
    content: Подключить новый роут и API-функцию фронта для загрузки карточки
    status: completed
  - id: update-feature-artifacts
    content: Обновить mandatory feature-документы и action-log по правилам проекта
    status: completed
isProject: false
---

# План: постеры в профиле и экран детали карточки

## Цель
Привести блоки карточек в моем и публичном профиле к виду «чистые постеры одинакового размера» и добавить переход в детальный экран карточки, визуально близкий к присланному макету (реальные данные + статические mock-блоки, которых пока нет в backend).

## Изменения backend
- Добавить endpoint получения одной карточки по id с авторизацией и проверкой видимости:
  - [backend/src/api/cards/routes.py](/Users/r.makkhmudov/Projects/github/kino/backend/src/api/cards/routes.py)
  - [backend/src/api/cards/schemas.py](/Users/r.makkhmudov/Projects/github/kino/backend/src/api/cards/schemas.py)
- В ответе деталки вернуть данные, достаточные для экрана:
  - `id`, `film_id`, `film_title`, `film_year`, `film_poster_url`, `rating`, `company`, `mood_before`, `mood_after`, `custom_tags`.
- Реализовать/переиспользовать сервис чтения карточки с join на `Film` и проверкой доступа текущего пользователя.
- Добавить тесты на новый endpoint:
  - happy path;
  - 401 без авторизации;
  - 404 при несуществующей карточке;
  - запрет/404 на чужую закрытую карточку (по текущей логике видимости).

## Изменения frontend
- Профили: заменить список `Cell` на сетку постеров фиксированного размера без текстовых подписей:
  - [frontend/src/pages/ProfilePage.tsx](/Users/r.makkhmudov/Projects/github/kino/frontend/src/pages/ProfilePage.tsx)
  - [frontend/src/pages/PublicProfilePage.tsx](/Users/r.makkhmudov/Projects/github/kino/frontend/src/pages/PublicProfilePage.tsx)
- Вынести общий UI постер-сетки в отдельный компонент (чтобы одинаково выглядело в двух профилях):
  - новый файл в `frontend/src/components/profile/` (например `MoviePosterGrid.tsx`).
- Добавить переход по клику на постер в деталку карточки (`/cards/:cardId`).
- Добавить новый экран детали карточки, близкий к макету:
  - новый файл `frontend/src/pages/MovieCardDetailPage.tsx`.
  - верхний блок: постер, название, год;
  - блок реальных данных: рейтинг, контекстные теги, custom tags;
  - блоки без backend-данных: статический mock (друзья оценили, лучшая оценка, комментарии, invite/recommend).
- Подключить маршрут:
  - [frontend/src/routes.tsx](/Users/r.makkhmudov/Projects/github/kino/frontend/src/routes.tsx)
- Добавить API-функцию загрузки карточки по id:
  - [frontend/src/api/cardApi.ts](/Users/r.makkhmudov/Projects/github/kino/frontend/src/api/cardApi.ts)
  - при необходимости дополнить типы в [frontend/src/api/profileTypes.ts](/Users/r.makkhmudov/Projects/github/kino/frontend/src/api/profileTypes.ts).

## UX/визуальные требования
- Все постеры в сетке одинаковые по пропорциям и размерам.
- В профилях в гриде показываем только изображение постера (без названий/рейтингов под ним).
- Деталка визуально повторяет структуру макета, но функциональность отсутствующих секций явно помечена как mock.

## Проверка
- Frontend ручной сценарий:
  - мой профиль: сетка одинаковых постеров -> клик -> открывается деталка;
  - публичный профиль: аналогично;
  - прямое открытие `/cards/:cardId` и refresh работают.
- Backend тесты внутри Docker по новому endpoint и регрессии существующих cards/profile flows.
- Линт по затронутым frontend/backend файлам.

## Артефакты фичи
- Обновить:
  - `.cursor/active/movie-card-create-flow/plan.md`
  - `.cursor/active/movie-card-create-flow/progress.md`
  - `.cursor/active/movie-card-create-flow/result.md`
  - `docs/features/movie-card-create-flow.md`
  - запись в `.cursor/memory/logs/action-log-*` по индексу `.cursor/memory/logs/action-log.md`.
