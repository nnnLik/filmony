# Feature: movie-card-create-flow

## Metadata
- Feature slug: `movie-card-create-flow`
- Source backlog: [`.cursor/features/004-kinopoisk-movie-by-link.md`](../../features/004-kinopoisk-movie-by-link.md), [`.cursor/features/005-movie-rating-with-tags.md`](../../features/005-movie-rating-with-tags.md)
- Priority: P1
- Target area: fullstack

## Problem
Нужен рабочий поток создания карточки фильма: получение фильма по ссылке Кинопоиска, создание карточки с контекстными тегами и оценкой 1..10 с шагом 0.5, отображение карточек на профилях.

## Scope
- In scope: `POST /api/films/resolve`, `GET /api/films/{film_id}`, `POST /api/cards`, реальный `GET /api/users/{user_id}/cards`, реальный `cards_count` в профиле, frontend экран создания карточки и точка входа из ленты.
- Out of scope: приглашения друзей «дооценить», комментарии/лайки, рекомендации.

## Functional Requirements
- [x] Оценка карточки валидируется в диапазоне 1..10 с шагом 0.5.
- [x] Повторный `POST /api/cards` для пары `(user_id, film_id)` возвращает `409`.
- [x] До 5 custom tags, с trim и дедупликацией.
- [x] Film resolve по ссылке Кинопоиска идемпотентно возвращает один и тот же фильм.
- [x] Фронт поддерживает URL -> preview -> create.

## Acceptance Criteria
- [x] Авторизованный пользователь создает карточку и видит ее в списке профиля.
- [x] Неавторизованный пользователь получает `401` на создание карточки и resolve.
- [x] Невалидная ссылка Кинопоиска возвращает `422`.
- [x] Дубликат карточки возвращает `409`.

## Constraints
- Docker-first для backend команд (`make backend-test*`).
- FastAPI бизнес-логика через service-классы.
- UI на `@telegram-apps/telegram-ui`.
