---
name: profile stats details
overview: Добавить полноценную статистику карточек фильмов в профиле (мой и публичный) с новым backend API агрегатов и отображением всех блоков на фронтенде.
todos:
  - id: backend-stats-service-api
    content: Спроектировать и добавить backend сервис агрегатов + endpoint /api/users/{user_id}/stats и схемы ответа
    status: completed
  - id: backend-tests
    content: Добавить/обновить API тесты профиля для нового stats endpoint и всех ключевых кейсов
    status: completed
  - id: frontend-stats-ui
    content: Подключить новый API в frontend и реализовать UI статистики в ProfilePage и PublicProfilePage через общий компонент
    status: completed
  - id: verification-and-artifacts
    content: Проверить сценарии и обновить обязательные feature-delivery артефакты
    status: completed
isProject: false
---

# Реализация статистики профиля пользователя

## Что делаем
Добавляем единый API агрегированной статистики по карточкам пользователя и подключаем его в обоих экранах профиля: `"Статистика"` в `"/profile"` и `"/u/:userId"`.

## Область изменений
- Backend API и схемы ответа:
  - [backend/src/api/profile/schemas.py](backend/src/api/profile/schemas.py)
  - [backend/src/api/profile/users_routes.py](backend/src/api/profile/users_routes.py)
- Backend бизнес-логика агрегатов:
  - [backend/src/services/profile/get_user_movie_card_stats.py](backend/src/services/profile/get_user_movie_card_stats.py) (новый)
- Backend тесты:
  - [backend/src/tests/api/test_profile_routes.py](backend/src/tests/api/test_profile_routes.py)
- Frontend API/types:
  - [frontend/src/api/profileApi.ts](frontend/src/api/profileApi.ts)
  - [frontend/src/api/profileTypes.ts](frontend/src/api/profileTypes.ts)
- Frontend UI статистики:
  - [frontend/src/components/profile/ProfileStatsPanel.tsx](frontend/src/components/profile/ProfileStatsPanel.tsx) (новый)
  - [frontend/src/pages/ProfilePage.tsx](frontend/src/pages/ProfilePage.tsx)
  - [frontend/src/pages/PublicProfilePage.tsx](frontend/src/pages/PublicProfilePage.tsx)

## Backend план
1. Добавить сервис `GetUserMovieCardStatsService` с одним публичным методом `execute(user_id)`:
   - общий итог: всего фильмов, средняя оценка;
   - распределение оценок (бакеты 1..10);
   - распределение по годам выпуска;
   - популярные теги (по `movie_card_tag`, топ-лимит);
   - «С кем смотрю» (по `movie_card.company`);
   - «Настроение после просмотра» (по `movie_card.mood_after`);
   - списки топ-5 и худших-5 фильмов (стабильная сортировка по рейтингу и id карточки).
2. Расширить схемы профиля отдельным `UserMovieCardStatsResponse` + вложенными item-моделями.
3. Добавить endpoint `GET /api/users/{user_id}/stats` в users router (auth required, `404 user not found`).
4. Покрыть тестами:
   - `401` без авторизации;
   - `404` для несуществующего пользователя;
   - happy-path агрегатов на наборе карточек (все блоки ответа);
   - проверка top/worst по стабильному порядку при равных оценках.

## Frontend план
1. Добавить типы и клиент `getUserMovieCardStats(userId)`.
2. Вынести UI статистики в `ProfileStatsPanel`:
   - карточки: «Всего фильмов», «Средняя оценка»;
   - блоки: распределение оценок, по годам, популярные теги, с кем смотрю, настроение после просмотра;
   - секции списков: «Топ фильмов» (5) и «Худший фильм» (5);
   - корректные empty/loading/error состояния.
3. Подключить панель в `ProfilePage` (вкладка `stats`) вместо текущей заглушки.
4. Добавить в `PublicProfilePage` вкладки `Фильмы/Статистика` и использовать тот же `ProfileStatsPanel` для целевого пользователя.

## Технические решения
- Используем один endpoint для обоих экранов (мой/публичный) для консистентности.
- Сохраняем существующую архитектуру: роут тонкий, бизнес-логика в сервисе.
- Для top/worst применяем стабильную сортировку (как согласовано: любой стабильный порядок).

## Проверка
- Backend: прогон `pytest` по профилю и связанных тестов внутри Docker-окружения проекта.
- Frontend: проверка рендера двух страниц (`/profile`, `/u/:userId`) на loading/empty/data/error сценариях.

## Артефакты workflow
В процессе реализации обновить обязательные файлы feature lifecycle:
- `.cursor/active/{feature-slug}/plan.md`
- `.cursor/active/{feature-slug}/progress.md`
- `.cursor/active/{feature-slug}/result.md`
- `docs/features/{feature-slug}.md`
- запись в `.cursor/memory/logs/` (по правилам проекта).
