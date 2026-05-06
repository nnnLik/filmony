# 2026-05-06T10:30:00Z

## 2026-05-06T05:12:00Z
- Feature slug: `movie-card-comments`
- Action type: plan | docs
- Summary: Созданы обязательные workflow-артефакты фичи (`feature.md`, `plan.md`, `progress.md`, `result.md`, `docs/features`).
- Files:
  - `.cursor/features/movie-card-comments/feature.md`
  - `.cursor/active/movie-card-comments/plan.md`
  - `.cursor/active/movie-card-comments/progress.md`
  - `.cursor/active/movie-card-comments/result.md`
  - `docs/features/movie-card-comments.md`
  - `.cursor/memory/logs/action-log-from-2026-05-06T103000Z.md`
- Verification:
  - Проверка наличия созданных файлов.
- Links:
  - `.cursor/active/movie-card-comments/progress.md`
  - `docs/features/movie-card-comments.md`

## 2026-05-06T05:18:00Z
- Feature slug: `movie-card-comments`
- Action type: code
- Summary: Реализованы backend сервисы и API для комментариев/ответов под карточкой с публичным чтением, auth-only созданием, валидацией текста, проверкой принадлежности parent и cursor пагинацией (`comments`, `replies`).
- Files:
  - `backend/src/services/cards/create_movie_card_comment.py`
  - `backend/src/services/cards/list_movie_card_comments.py`
  - `backend/src/services/cards/__init__.py`
  - `backend/src/api/cards/schemas.py`
  - `backend/src/api/cards/routes.py`
  - `backend/src/tests/api/test_cards_routes.py`
  - `.cursor/active/movie-card-comments/progress.md`
  - `.cursor/active/movie-card-comments/result.md`
  - `docs/features/movie-card-comments.md`
  - `.cursor/memory/logs/action-log-from-2026-05-06T103000Z.md`
- Verification:
  - `ReadLints` по изменённым backend-файлам: ошибок нет.
- Links:
  - `.cursor/active/movie-card-comments/progress.md`
  - `docs/features/movie-card-comments.md`

## 2026-05-06T05:19:00Z
- Feature slug: `movie-card-comments`
- Action type: code
- Summary: Добавлен индекс ветвления комментариев `(movie_card_id, parent_comment_id, id)` в модели и отдельной Alembic-миграции.
- Files:
  - `backend/src/models/movie_card_comment.py`
  - `backend/src/migrations/versions/c9d2e8a1b7c3_comment_branch_index.py`
  - `.cursor/active/movie-card-comments/progress.md`
  - `.cursor/active/movie-card-comments/result.md`
  - `.cursor/memory/logs/action-log-from-2026-05-06T103000Z.md`
- Verification:
  - `ReadLints` по изменённым backend-файлам: ошибок нет.
- Links:
  - `.cursor/active/movie-card-comments/progress.md`
  - `docs/features/movie-card-comments.md`

## 2026-05-06T05:20:00Z
- Feature slug: `movie-card-comments`
- Action type: test | docs
- Summary: Зафиксирована попытка Docker-first проверки, но shell-команды отклонены средой; обновлены result/docs с прозрачным статусом верификации.
- Files:
  - `.cursor/active/movie-card-comments/progress.md`
  - `.cursor/active/movie-card-comments/result.md`
  - `docs/features/movie-card-comments.md`
  - `.cursor/memory/logs/action-log-from-2026-05-06T103000Z.md`
- Verification:
  - `Shell: ls` -> `Rejected: User chose to skip`.
- Links:
  - `.cursor/active/movie-card-comments/progress.md`
  - `docs/features/movie-card-comments.md`

## 2026-05-06T04:40:00Z
- Feature slug: `profile-address-lockdown`
- Action type: refactor | code
- Summary: Убрана возможность менять публичный адрес: PATCH `/api/me/profile` больше не принимает `profile_slug`; удалён backend endpoint профиля по slug; фронт переведён на переходы по `user_id` (`/u/:userId`) и убрано поле редактирования публичного адреса из экрана редактирования профиля.
- Files:
  - `backend/src/api/profile/schemas.py`
  - `backend/src/services/profile/update_my_profile.py`
  - `backend/src/api/profile/me_routes.py`
  - `backend/src/api/profile/users_routes.py`
  - `backend/src/tests/api/test_profile_routes.py`
  - `frontend/src/lib/publicProfileUrl.ts`
  - `frontend/src/api/profileApi.ts`
  - `frontend/src/routes.tsx`
  - `frontend/src/pages/PublicProfilePage.tsx`
  - `frontend/src/pages/SubscriptionsPage.tsx`
  - `frontend/src/pages/ProfileEditPage.tsx`
  - `.cursor/memory/logs/action-log-from-2026-05-06T103000Z.md`
- Verification:
  - `ReadLints` по изменённым backend/frontend файлам: ошибок нет.
- Links:
  - `backend/src/tests/api/test_profile_routes.py`
  - `frontend/src/pages/ProfileEditPage.tsx`

## 2026-05-06T22:00:00Z
- Feature slug: `telegram-mini-app-ui`
- Action type: code | docs
- Summary: Тёмная палитра Filmony и переопределение tgui-токенов; плавающий нижний навбар; кеш sessionStorage для оптимистичного auth и бандла «мой профиль + карточки»; экран `/profile/edit` из шестерёнки; публичная ссылка по тапу копирует URL + Snackbar; класс `.filmony-text-panel` для вторичных текстов; доработки публичного профиля и хедера.
- Files:
  - `frontend/src/index.css`
  - `frontend/src/App.tsx`
  - `frontend/src/layout/AppShell.tsx`
  - `frontend/src/components/navigation/BottomNav.tsx`
  - `frontend/src/auth/AuthProvider.tsx`
  - `frontend/src/lib/filmonySession.ts`
  - `frontend/src/lib/myProfileBundleCache.ts`
  - `frontend/src/lib/publicProfileUrl.ts`
  - `frontend/src/pages/ProfilePage.tsx`
  - `frontend/src/pages/ProfileEditPage.tsx`
  - `frontend/src/pages/FeedPage.tsx`
  - `frontend/src/pages/PublicProfilePage.tsx`
  - `frontend/src/components/profile/ProfileHeader.tsx`
  - `frontend/src/routes.tsx`
  - `.cursor/memory/features/telegram-mini-app-ui.md`
  - `.cursor/memory/logs/action-log-from-2026-05-06T103000Z.md`
- Verification: рекомендуется `cd frontend && npm run build && npm run lint` (в сессии не зафиксировано).
- Links:
  - `.cursor/memory/features/telegram-mini-app-ui.md`

## 2026-05-06T18:30:00Z
- Feature slug: `profile-and-public-profiles`
- Action type: code | docs
- Summary: Реализация профилей (API, миграция, тесты), фронт (Router, Telegram UI, AuthProvider), исправление ревизии Alembic на ALTER+backfill, публикация `docs/features/profile-and-public-profiles.md` и артефактов `.cursor/active/profile-and-public-profiles/*`, `.cursor/features/profile-and-public-profiles/feature.md`.
- Files:
  - `backend/src/migrations/versions/110da8652616_enchant_user.py`
  - `backend/src/api/profile/*`, `backend/src/services/profile/*`, `backend/src/models/user.py`, `backend/src/services/auth/upsert_telegram_user.py`, `backend/src/api/router.py`, `backend/src/conf/settings.py`
  - `backend/src/tests/api/test_profile_routes.py`
  - `frontend/package.json`, `frontend/src/App.tsx`, `frontend/src/main.tsx`, `frontend/src/routes.tsx`, `frontend/src/pages/*`, `frontend/src/api/*`, `frontend/src/auth/*`, `frontend/src/components/profile/*`, `frontend/src/lib/profileDisplay.ts`
  - `vars/.env.example`, `docs/features/profile-and-public-profiles.md`
  - `.cursor/features/profile-and-public-profiles/feature.md`, `.cursor/active/profile-and-public-profiles/plan.md`, `.cursor/active/profile-and-public-profiles/progress.md`, `.cursor/active/profile-and-public-profiles/result.md`
- Verification: **не запускалось** (по запросу пользователя без команд); рекомендуется `npm install`, `npm run build`, `make backend-test`.
- Links:
  - `.cursor/active/profile-and-public-profiles/result.md`
  - `docs/features/profile-and-public-profiles.md`

## 2026-05-06T12:00:00Z
- Feature slug: `telegram-user-base`
- Action type: docs
- Summary: Созданы артефакты workflow: `feature.md` по slug, `plan.md`, `progress.md`, `result.md`, публикация `docs/features/telegram-user-base.md`.
- Files:
  - `.cursor/features/telegram-user-base/feature.md`
  - `.cursor/active/telegram-user-base/plan.md`
  - `.cursor/active/telegram-user-base/progress.md`
  - `.cursor/active/telegram-user-base/result.md`
  - `docs/features/telegram-user-base.md`
  - `.cursor/memory/logs/action-log-from-2026-05-06T103000Z.md`
- Verification: проверка наличия путей в репозитории.
- Links:
  - `.cursor/active/telegram-user-base/progress.md`
  - `docs/features/telegram-user-base.md`

## 2026-05-06T11:30:00Z
- Feature slug: `repo-hygiene`
- Action type: docs
- Summary: Корневой `.gitignore` (Python, Node, IDE, env), `README.md`, шаблон `vars/.env.example`.
- Files:
  - `.gitignore`
  - `README.md`
  - `vars/.env.example`
- Verification: шаблон без секретов; `vars/.env.*` игнорируются с исключением `.env.example`.

## 2026-05-06T11:00:00Z
- Feature slug: `telegram-user-base`
- Action type: refactor
- Summary: Убрано затенение `BaseSettings.schema`: поле переименовано в `default_schema`, env остаётся `DATABASE_SCHEMA`; правка `core/database.py`.
- Files:
  - `backend/src/conf/settings.py`
  - `backend/src/core/database.py`
- Verification: предупреждение Pydantic при старте Uvicorn не воспроизводится (логи Docker).

## 2026-05-06T10:30:00Z
- Feature slug: `telegram-user-base`
- Action type: refactor
- Summary: Режим тестов через `ENV=test` и `DatabaseSettings`; убран глобальный `_testing`; DDL для pytest только в `src/tests/conftest.py`; PostgreSQL-only.
- Files:
  - `backend/src/conf/settings.py`
  - `backend/src/core/database.py`
  - `backend/src/tests/conftest.py`
- Verification: ожидается `make backend-test` в контейнере (см. `.cursor/tech.md`).

## 2026-05-06T04:58:00Z
- Feature slug: `movie-card-create-flow`
- Action type: code | docs
- Summary: Лента упрощена; экран создания карточки переработан в нумерованный wizard из 5 шагов с confirm-этапом после resolve URL, понятными ошибками парсинга Кинопоиска, этапом рейтинга+chips-тегов, этапом custom tags и mock-этапом перед финальным созданием карточки.
- Files:
  - `frontend/src/pages/CreateCardPage.tsx`
  - `frontend/src/pages/FeedPage.tsx`
  - `.cursor/active/movie-card-create-flow/plan.md`
  - `.cursor/active/movie-card-create-flow/progress.md`
  - `.cursor/active/movie-card-create-flow/result.md`
  - `docs/features/movie-card-create-flow.md`
  - `.cursor/memory/logs/action-log-from-2026-05-06T103000Z.md`
- Verification:
  - `ReadLints` по `frontend/src/pages/CreateCardPage.tsx`, `frontend/src/pages/FeedPage.tsx` — ошибок нет.
- Links:
  - `.cursor/active/movie-card-create-flow/progress.md`
  - `docs/features/movie-card-create-flow.md`

## 2026-05-06T05:10:00Z
- Feature slug: `movie-card-create-flow`
- Action type: code | docs
- Summary: Добавлен backend `GET /api/cards/{card_id}` и frontend деталка карточки с deep-link маршрутом; карточки в моем и публичном профиле переведены в единый грид одинаковых постеров с переходом по клику; на деталке добавлены real-data секции и статические mock-блоки по референсу.
- Files:
  - `backend/src/api/cards/routes.py`
  - `backend/src/api/cards/schemas.py`
  - `backend/src/services/cards/get_movie_card_details.py`
  - `backend/src/tests/api/test_cards_routes.py`
  - `frontend/src/components/profile/MoviePosterGrid.tsx`
  - `frontend/src/pages/ProfilePage.tsx`
  - `frontend/src/pages/PublicProfilePage.tsx`
  - `frontend/src/pages/MovieCardDetailPage.tsx`
  - `frontend/src/routes.tsx`
  - `frontend/src/api/cardApi.ts`
  - `.cursor/active/movie-card-create-flow/plan.md`
  - `.cursor/active/movie-card-create-flow/progress.md`
  - `.cursor/active/movie-card-create-flow/result.md`
  - `docs/features/movie-card-create-flow.md`
  - `.cursor/memory/logs/action-log-from-2026-05-06T103000Z.md`
- Verification:
  - `ReadLints` по измененным backend/frontend файлам — ошибок нет.
  - Shell-команды на запуск тестов/сборки в этой сессии недоступны (пропускаются средой).
- Links:
  - `.cursor/active/movie-card-create-flow/progress.md`
  - `docs/features/movie-card-create-flow.md`

## 2026-05-06T05:30:00Z
- Feature slug: `movie-card-create-flow`
- Action type: code | docs
- Summary: Переработан UI оценки на деталке (одно число + динамический цветовой акцент), удален блок "Лучшая оценка", внедрена полноценная система комментариев с хранением в БД, древовидными ответами, многострочным вводом (<=250), отображением автора/аватарки/времени и переходом на профиль автора.
- Files:
  - `backend/src/models/movie_card_comment.py`
  - `backend/src/migrations/versions/d3d7c8a2ef11_add_movie_card_comments.py`
  - `backend/src/api/cards/routes.py`
  - `backend/src/api/cards/schemas.py`
  - `backend/src/services/cards/create_movie_card_comment.py`
  - `backend/src/services/cards/list_movie_card_comments.py`
  - `backend/src/tests/api/test_cards_routes.py`
  - `backend/src/models/__init__.py`
  - `frontend/src/api/cardApi.ts`
  - `frontend/src/api/profileTypes.ts`
  - `frontend/src/pages/MovieCardDetailPage.tsx`
  - `.cursor/active/movie-card-create-flow/progress.md`
  - `.cursor/active/movie-card-create-flow/result.md`
  - `docs/features/movie-card-create-flow.md`
  - `.cursor/memory/logs/action-log-from-2026-05-06T103000Z.md`
- Verification:
  - `ReadLints` по измененным backend/frontend файлам — ошибок нет.
- Links:
  - `.cursor/active/movie-card-create-flow/progress.md`
  - `docs/features/movie-card-create-flow.md`
