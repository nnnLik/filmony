# Result — profile-and-public-profiles

## Feature
- Slug: `profile-and-public-profiles`
- Final status: **done** (включая публичные полки; полный backend suite не гонялся в этой сессии)

## Implemented

### Базовый контур (исторический)
- Расширена модель пользователя: `profile_slug`, `display_name`, `bio`; уникальный индекс по slug; миграция с backfill slug для существующих строк.
- `GET/PATCH /api/me/profile` — полный редактируемый профиль и счётчики; `GET /api/users/{user_id}` — публичный профиль (404 если нет).
- Фронт: маршруты `/profile`, `/u/:identifier`, TMA-сессия через cookie.

### Срез 2026-05-25: полки на публичном профиле
- **`GET /api/users/{user_id}/card-categories`** — авторизованный зритель получает те же формы объектов (`id`, `name`, `created_at`), что и в `/api/me/card-categories`, но **без побочного создания дефолтной полки**; только чтение уже существующих строк для `owner_user_id`. Несуществующий пользователь — **404**.
- **`ListPublicUserCardCategoriesService`** — сервис-оркестратор: сортировка по имени, затем по `id`; без транспортной логики.
- **Фронт:** `getUserPublicCardCategories(userId)`, ключ `publicProfileCardCategoriesQueryKey(userId)`. В `ProfileRatedCardsFilters`: если включён фильтр по полке и **зритель = владелец профиля** → `GET /api/me/card-categories` (как раньше); иначе → публичная ручка для `profileUserId`. На **`PublicProfilePage`** фильтр полок включён для всех; на **`ProfilePage`** передаётся `viewerUserId={profile.id}`.

## Changed Files (срез 2026-05-25)

- `backend/src/services/user_card_categories/list_public_user_card_categories.py` (новый)
- `backend/src/services/user_card_categories/__init__.py`
- `backend/src/api/profile/users_routes.py`
- `backend/src/tests/api/test_profile_routes.py`
- `frontend/src/api/profileApi.ts`
- `frontend/src/api/profileTypes.ts`
- `frontend/src/feed/feedQueryKeys.ts`
- `frontend/src/components/profile/ProfileRatedCardsFilters.tsx`
- `frontend/src/pages/PublicProfilePage.tsx`
- `frontend/src/pages/ProfilePage.tsx`
- `docs/features/profile-and-public-profiles.md`
- `.cursor/active/profile-and-public-profiles/plan.md`, `progress.md`, `result.md`
- `.cursor/memory/logs/2026-05-25T190530Z-profile-and-public-profiles-code.md`
- `.cursor/memory/logs/2026-05-25T190545Z-profile-and-public-profiles-test.md`
- `.cursor/memory/logs/2026-05-25T190600Z-profile-and-public-profiles-docs.md`

## Verification

Commands executed in this session:

- `docker exec -w /opt/app/src filmony-backend pytest tests/api/test_profile_routes.py::test_public_user_card_categories_requires_auth tests/api/test_profile_routes.py::test_public_user_card_categories_404_unknown_user tests/api/test_profile_routes.py::test_public_user_card_categories_returns_owner_shelves tests/api/test_profile_routes.py::test_public_user_card_categories_lists_committed_shelves -q` — passed
- `docker exec -w /opt/app/src filmony-backend ruff check --fix --config /opt/app/pyproject.toml api/profile/users_routes.py` — OK
- `cd frontend && npm run lint && npm run build && npm test` — passed (`vitest`: 1 file)

Recommended before merge: `make backend-test`, `make backend-lint`.

## Automated tests

- **`backend/src/tests/api/test_profile_routes.py`** — новые случаи: `test_public_user_card_categories_*`.

## Known limitations

- Ответ `/api/me/card-categories` может показывать дефолтную полку в рамках одного запроса до отката сессии, если приложение не коммитает в конце запроса; публичный список отражает **закоммиченное** состояние. Тест документирует ожидание после `POST`-создания полки.

## Архив: фронт Mini App (2026-05-06)

Дополнения к экранам профиля и общему UI мини-приложения зафиксированы в памяти проекта:

- `.cursor/memory/features/telegram-mini-app-ui.md` — палитра, навбар, кеш auth/профиля, `/profile/edit`, копирование публичной ссылки, `.filmony-text-panel`.
- Запись в `.cursor/memory/logs/action-log-from-2026-05-06T103000Z.md` (slug `telegram-mini-app-ui`, метка времени 2026-05-06T22:00:00Z).
