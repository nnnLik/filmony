# Result — profile-and-public-profiles

## Feature
- Slug: `profile-and-public-profiles`
- Final status: **done** (публичные полки + ленивая загрузка и клиентский кеш списка полок; см. ниже).

## Implemented

### Базовый контур (исторический)
- Расширена модель пользователя: `profile_slug`, `display_name`, `bio`; уникальный индекс по slug; миграция с backfill slug для существующих строк.
- `GET/PATCH /api/me/profile` — полный редактируемый профиль и счётчики; `GET /api/users/{user_id}` — публичный профиль (404 если нет).
- Фронт: маршруты `/profile`, `/u/:identifier`, TMA-сессия через cookie.

### Срез 2026-05-25: полки на публичном профиле
- **`GET /api/users/{user_id}/card-categories`** — авторизованный зритель получает те же формы объектов (`id`, `name`, `created_at`), что и в `/api/me/card-categories`, но **без побочного создания дефолтной полки**; только чтение уже существующих строк для `owner_user_id`. Несуществующий пользователь — **404**.
- **`ListPublicUserCardCategoriesService`** — сервис-оркестратор: сортировка по имени, затем по `id`; без транспортной логики.
- **Фронт:** `getUserPublicCardCategories(userId)`, ключ `publicProfileCardCategoriesQueryKey(userId)`. В `ProfileRatedCardsFilters`: если включён фильтр по полке и **зритель = владелец профиля** → `GET /api/me/card-categories` (как раньше); иначе → публичная ручка для `profileUserId`. На **`PublicProfilePage`** фильтр полок включён для всех; на **`ProfilePage`** передаётся `viewerUserId={profile.id}`.

### Срез 2026-05-25 (кеш полок на клиенте)
- Полки запрашиваются **только** после раскрытия панели фильтров (`ProfileRatedCardsFilters`, `filtersOpen`) или блока доп. фильтров в статистике (`ProfileStatsFilters`, `moreOpen`); ключи React Query те же (`myCardCategoriesQueryKey`, `publicProfileCardCategoriesQueryKey`).
- React Query: `staleTime` **15 мин**, `gcTime` **60 мин**, запись успешных ответов в **sessionStorage** (`frontend/src/lib/userCardCategoriesStorage.ts`) как `placeholderData` (аналог паттерна тегов карточек).
- При сбросе сессии/ошибках входа — `clearUserCardCategoriesSessionCaches()` вместе с очисткой кеша статистики тегов (`AuthProvider`).

## Changed Files (исторический срез API + документация 2026-05-25)

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

## Changed Files (клиентский кеш полок, 2026-05-25)

- `frontend/src/lib/userCardCategoriesStorage.ts` (новый)
- `frontend/src/components/profile/ProfileRatedCardsFilters.tsx`
- `frontend/src/components/profile/ProfileStatsFilters.tsx`
- `frontend/src/auth/AuthProvider.tsx`
- `docs/features/profile-and-public-profiles.md`
- `.cursor/active/profile-and-public-profiles/progress.md`, `result.md`
- `.cursor/memory/logs/2026-05-25T201200Z-profile-and-public-profiles-code.md`
- `.cursor/memory/logs/2026-05-25T201210Z-profile-and-public-profiles-docs.md`
- `.cursor/memory/logs/action-log.md`

## Verification

Последний прогон (сессия кеша полок, без изменений API):

- `cd frontend && npm run lint && npm run build` — OK
- `cd frontend && npm test -- --run` — OK (1 файл)

Исторически для ручки `GET .../card-categories`:

- Ранее: `pytest` по `tests/api/test_profile_routes.py` для `card-categories` — passed (контракт API в этом изменении не трогали).

Recommended before merge: `make backend-test`, `make backend-lint`.

## Automated tests

- **`backend/src/tests/api/test_profile_routes.py`** — новые случаи: `test_public_user_card_categories_*`.

## Known limitations

- Ответ `/api/me/card-categories` может показывать дефолтную полку в рамках одного запроса до отката сессии, если приложение не коммитает в конце запроса; публичный список отражает **закоммиченное** состояние. Тест документирует ожидание после `POST`-создания полки.

## Архив: фронт Mini App (2026-05-06)

Дополнения к экранам профиля и общему UI мини-приложения зафиксированы в памяти проекта:

- `.cursor/memory/features/telegram-mini-app-ui.md` — палитра, навбар, кеш auth/профиля, `/profile/edit`, копирование публичной ссылки, `.filmony-text-panel`.
- Запись в `.cursor/memory/logs/action-log-from-2026-05-06T103000Z.md` (slug `telegram-mini-app-ui`, метка времени 2026-05-06T22:00:00Z).
