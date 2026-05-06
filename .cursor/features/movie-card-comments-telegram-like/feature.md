# Feature Request

## Metadata
- Feature slug: `movie-card-comments-telegram-like`
- Author: Codex
- Created at: 2026-05-06 20:25 UTC
- Priority: high
- Target area: fullstack

## Problem
- Текущая система комментариев в карточке фильма построена как дерево с отдельной страницей ветки.
- Такой UX сложнее для чтения в мобильном контексте Telegram Mini App и не соответствует ожидаемой модели "ответ на сообщение".

## Scope
- In scope:
  - Плоская выдача комментариев карточки через основной endpoint.
  - Telegram-like отображение ответа с компактным preview родительского комментария.
  - Переход к родительскому комментарию по нажатию на preview с автодогрузкой и скроллом.
  - Удаление отдельной страницы thread из пользовательского потока.
- Out of scope:
  - Реакции/лайки комментариев.
  - Изменение модели хранения комментариев в БД.
  - Реалтайм-обновления комментариев.

## Functional Requirements
- [ ] `GET /api/cards/{card_id}/comments` возвращает плоский список комментариев карточки с пагинацией.
- [ ] UI карточки рендерит комментарии единым списком без вложенных уровней.
- [ ] Для комментариев с `parent_comment_id` в UI отображается preview родителя.
- [ ] Нажатие на preview переводит к родительскому комментарию и визуально подсвечивает его.
- [ ] Если родитель не загружен, UI автоматически догружает страницы до нахождения или исчерпания списка.

## Acceptance Criteria
- [ ] Древовидный UI и переход на отдельную thread-страницу отсутствуют в основном пользовательском сценарии.
- [ ] Reply-preview визуально отделен и читается как "ответ на сообщение".
- [ ] Parent jump работает для уже загруженных и догруженных родителей.
- [ ] Создание root/reply комментариев сохраняет корректный `parent_comment_id`.
- [ ] API и UI проверки проходят без регрессий.

## Constraints
- Technical constraints:
  - Сохранить обратную совместимость модели данных (`parent_comment_id`).
  - Backend тесты запускать в Docker окружении проекта.
- Product/design constraints:
  - Стилистика близка к Telegram reply UX в рамках текущего UI-кита.
  - Интерфейс рассчитан на мобильный экран Mini App.

## References
- Related issue/ticket: `.cursor/user-story.md`
- Related files/modules:
  - `backend/src/api/cards/routes.py`
  - `backend/src/services/cards/list_movie_card_comments.py`
  - `backend/src/tests/api/test_cards_routes.py`
  - `frontend/src/pages/MovieCardDetailPage.tsx`
  - `frontend/src/routes.tsx`
