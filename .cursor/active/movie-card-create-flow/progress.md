# Progress: movie-card-create-flow

## Feature
- Slug: `movie-card-create-flow`
- Status: done

## Action Entries
### 2026-05-06 04:45
- Action type: code
- Summary: Добавлены backend модели фильмов/карточек/тегов, сервис создания карточки, роуты cards/films и реальный листинг карточек профиля с подсчетом `cards_count`.
- Files:
  - `backend/src/models/film.py`
  - `backend/src/models/movie_card.py`
  - `backend/src/models/movie_card_tag.py`
  - `backend/src/models/movie_card_enums.py`
  - `backend/src/services/cards/create_movie_card.py`
  - `backend/src/services/profile/list_user_movie_cards.py`
  - `backend/src/services/profile/get_user_profile_counts.py`
  - `backend/src/api/cards/routes.py`
  - `backend/src/api/films/routes.py`
  - `backend/src/api/router.py`
  - `backend/src/migrations/versions/5d6f7a8b9c10_add_films_and_movie_cards.py`
- Verification:
  - `ReadLints` по `backend/src` — ошибок нет.
- Notes:
  - Команды в терминале были пропущены средой, поэтому backend pytest отмечен как рекомендованный для ручного прогона.

### 2026-05-06 04:55
- Action type: code
- Summary: Реализован frontend flow `/cards/new`: resolve URL, preview фильма, форма оценки шагом 0.5, контекстные теги, custom tags, отправка в `POST /api/cards`, инвалидация profile cache; включена точка входа из ленты.
- Files:
  - `frontend/src/pages/CreateCardPage.tsx`
  - `frontend/src/routes.tsx`
  - `frontend/src/pages/FeedPage.tsx`
  - `frontend/src/api/cardApi.ts`
  - `frontend/src/api/profileTypes.ts`
  - `frontend/src/pages/ProfilePage.tsx`
  - `frontend/src/pages/PublicProfilePage.tsx`
- Verification:
  - `ReadLints` по `frontend/src` — ошибок нет.
- Notes:
  - Команды `npm run lint`/`npm run build` не удалось выполнить из-за пропуска shell-команд средой.
