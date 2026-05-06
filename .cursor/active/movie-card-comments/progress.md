# Progress: movie-card-comments

## Feature
- Slug: `movie-card-comments`
- Status: done

## Action Entries
### 2026-05-06 05:12
- Action type: plan | docs
- Summary: Зафиксирован feature slug и созданы обязательные workflow-артефакты (`feature`, `plan`, `progress`).
- Files:
  - `.cursor/features/movie-card-comments/feature.md`
  - `.cursor/active/movie-card-comments/plan.md`
  - `.cursor/active/movie-card-comments/progress.md`
- Verification:
  - Проверка наличия файлов в репозитории.

### 2026-05-06 05:18
- Action type: code
- Summary: Обновлены backend комментарии под карточкой фильма: сервисы создания и листинга веток с cursor pagination, публичные endpoints чтения (`comments`, `replies`), auth-only создание, валидация текста и проверка parent на принадлежность карточке.
- Files:
  - `backend/src/services/cards/create_movie_card_comment.py`
  - `backend/src/services/cards/list_movie_card_comments.py`
  - `backend/src/services/cards/__init__.py`
  - `backend/src/api/cards/routes.py`
  - `backend/src/api/cards/schemas.py`
  - `backend/src/tests/api/test_cards_routes.py`
- Verification:
  - `ReadLints` по изменённым backend-файлам — ошибок нет.

### 2026-05-06 05:19
- Action type: code
- Summary: Добавлен индекс для веток комментариев в модели и новой Alembic-миграции для ускорения курсорного листинга (`movie_card_id`, `parent_comment_id`, `id`).
- Files:
  - `backend/src/models/movie_card_comment.py`
  - `backend/src/migrations/versions/c9d2e8a1b7c3_comment_branch_index.py`
- Verification:
  - `ReadLints` по изменённым backend-файлам — ошибок нет.

### 2026-05-06 05:20
- Action type: test
- Summary: Попытка запустить backend проверки в docker-контуре (`make backend-test*`) была отклонена средой (shell commands skipped), поэтому в сессии зафиксирована только статическая проверка через lints.
- Files:
  - `.cursor/active/movie-card-comments/progress.md`
- Verification:
  - `Shell: ls` в корне репозитория -> `Rejected: User chose to skip`.

### 2026-05-06 05:32
- Action type: code
- Summary: Добавлен `total_descendants_count` в backend контракт комментариев; сервис листинга считает общее число потомков через recursive CTE, роуты и схемы расширены новым полем.
- Files:
  - `backend/src/services/cards/list_movie_card_comments.py`
  - `backend/src/api/cards/schemas.py`
  - `backend/src/api/cards/routes.py`
  - `backend/src/tests/api/test_cards_routes.py`
- Verification:
  - `ReadLints` по backend файлам — ошибок нет.

### 2026-05-06 05:38
- Action type: code
- Summary: Исправлен баг отображения ответов на фронте: `MovieCardDetailPage` переведена на поуровневую загрузку (`roots + replies`), добавлена пагинация веток, кнопка перехода в отдельный экран при `total_descendants_count > 4`.
- Files:
  - `frontend/src/pages/MovieCardDetailPage.tsx`
  - `frontend/src/api/cardApi.ts`
  - `frontend/src/api/profileTypes.ts`
- Verification:
  - `ReadLints` по frontend файлам — ошибок нет.

### 2026-05-06 05:40
- Action type: code
- Summary: Добавлен отдельный экран ветки комментария и маршрут `/cards/:cardId/comments/:commentId/thread` для просмотра длинной дискуссии без UI-ограничения глубины на карточке.
- Files:
  - `frontend/src/pages/MovieCardCommentThreadPage.tsx`
  - `frontend/src/routes.tsx`
- Verification:
  - `ReadLints` по frontend файлам — ошибок нет.

### 2026-05-06 05:41
- Action type: test
- Summary: Попытка запуска целевого backend-теста в docker-контуре отклонена средой; верификация ограничена линт-диагностикой.
- Files:
  - `.cursor/active/movie-card-comments/progress.md`
- Verification:
  - `make backend-test-one target=src/tests/api/test_cards_routes.py` -> `Rejected: User chose to skip`.
