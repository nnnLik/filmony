# Movie card custom reactions

## Goal
Реакции на **карточки фильмов** и **комментарии** только из **каталога кастомных картинок** в БД. Стандартные emoji-мессенджера как дефолтный набор не используются.

## Data model
- **`reaction_type`**: `id`, `created_at`, `label` (опционально), `category_slug` (вкладка пикера), `asset_key` (S3-ключ относительно публичного base, например `reactions/pepe/foo.png`), `image_url` (fallback если base или asset пустые), `sort_order`, `is_active`.
- **`user_reaction`**: несколько строк на пару пользователь + цель с **разными** `reaction_type_id`. Уникальность: **`(user_id, target_kind, target_id, reaction_type_id)`**.
- **`user_recent_reaction`**: последнее использование типа пользователем (`user_id`, `reaction_type_id`, `last_used_at`, unique на пару). Обновляется при каждом `POST /api/reactions` для данных `reaction_type_id` (постановка и снятие), чтобы блок «Недавние» в каталоге сортировался по активности.

## Behaviour
- На одну карточку или комментарий пользователь может поставить **несколько** разных типов реакций; каждый тип **переключается отдельно** (повторный `POST` с тем же `reaction_type_id` снимает только эту реакцию).
- Self-react разрешён (флаг в `SetOrToggleUserReactionService`).
- Уведомления в Telegram **вне scope**; хук возможен через комментарий в сервисе после commit.

## CDN / RustFS (dev)
- В `docker-compose.yml` сервис **`rustfs`** (образ `rustfs/rustfs:1.0.0-beta.1`), том `rustfs-data`, хост-порты **7900→9000**, **7901→9001**.
- Для прямых публичных URL (без прокси) с path-style клиент собирает: `{REACTION_MEDIA_PUBLIC_BASE_URL}/{asset_key}` (без двойных слешей). Пример base: `http://127.0.0.1:7900/filmony-reactions`. Mini App без LAN к этому адресу: либо **прокси бэкенда**, либо отдельный HTTPS-домен к RustFS на том же origin, что и API.
- С **прокси** при `RUSTFS_INTERNAL_BASE_URL` и наличии **`RUSTFS_ACCESS_KEY`/`RUSTFS_SECRET_KEY`** у backend (см. `vars/.env.development`): в каталоге API отдаются **постоянные** относительные URL **`/api/reactions/asset/<asset_key>`** (без срока действия). Бэкенд забирает объект из контейнерного RustFS методом **S3 GetObject с SigV4** (не анонимный HTTP GET). Если ключи из env пустые, остаётся вырожденный путь через «голый» `httpx` (тогда при приватном бакете клиент будет получать ошибки загрузки).
- Если задан только **`REACTION_MEDIA_PUBLIC_BASE_URL`** (без внутреннего URL или без `asset_key`), клиент строит публичные ссылки напрямую к RustFS; для Mini App с телефона обычно неудобно из‑за `127.0.0.1` / приватности бакета — предпочтителен прокси без истечения срока.
- Сидеры в [`fixtures/reaction_type.sql`](/fixtures/reaction_type.sql) задают **`asset_key`** под объекты, которые можно залить `make sync-reactions-rustfs` или **`make sync-reactions-rustfs WITH_DB=1`** (см. [`scripts/upload_reactions_to_rustfs.py`](/scripts/upload_reactions_to_rustfs.py)).
- Политику **анонимного чтения** префикса `reactions/*` в RustFS нужно включать только если вы сознательно раздаёте картинки без прокси; для режима SigV4 из backend она не требуется.
- Порядок вкладок и каталоги emoji: **`backend/src/const/reaction_packs.py`** (маппинг `category_slug` ↔ папка в `emoji/`).

## API
### `GET /api/reactions/catalog`
Требует аутентификацию. Ответ:

```json
{
  "recent": [{ "id", "label", "image_url", "category_slug", "asset_key" }],
  "tabs": [
    { "category_slug": "pepe", "label": "Pepe", "items": [ … ] }
  ]
}
```

Только строки с `is_active = true`. Вкладки фиксированного порядка (см. `REACTION_TAB_ORDER`); в каждую попадают типы с совпадающим `category_slug`. `recent` — до 48 последних по `last_used_at` для текущего пользователя.

### `GET /api/reactions/actors`
Query: `target_kind`, `target_id`, `reaction_type_id`, опционально `limit` (1–50, по умолчанию 50). Ответ: `{ "items": [{ "id", "profile_slug", "display_name", "username", "first_name", "last_name", "photo_url" }] }` — для тултипа «кто реагировал» (лента не раздувается).

### `POST /api/reactions`
Тело:

```json
{
  "target_kind": "movie_card",
  "target_id": 123,
  "reaction_type_id": 1
}
```

Ответ:

```json
{
  "target_kind": "movie_card",
  "target_id": 123,
  "reactions": {
    "counts": [
      { "reaction_type_id": 1, "count": 2, "image_url": "…", "label": "…" }
    ],
    "my_reaction_type_ids": [1, 7]
  }
}
```

`image_url` в счётчиках собирается из `asset_key` + `REACTION_MEDIA_PUBLIC_BASE_URL`, иначе используется `image_url` из БД.

Ошибки: неизвестная/выключенная реакция — **422**, цель не найдена — **404**, некорректный `target_kind` — **422**.

### Вложенные поля в существующие ответы
Поле **`reactions`** того же вида добавлено к:
- `GET /api/cards/feed` (карточка и каждый элемент `comments_preview`);
- `GET /api/cards/{id}`;
- `GET /api/cards/{id}/comments` и replies.

Агрегаты считаются батчем в **`GetReactionSummariesForTargetsService`** (без N+1 на число типов или комментариев на странице).

**Требование к клиенту:** списки комментариев и replies вызываются **с авторизованной сессией** (как лента).

## Fixtures
- Сначала залить объекты в RustFS (и опционально в БД): `make sync-reactions-rustfs` или `make sync-reactions-rustfs WITH_DB=1`; при втором хост **homelab-postgres:5432** подменяется на **127.0.0.1:15432** (см. `Makefile`).
- После миграций: `fixtures/reaction_type.sql` или ручные `INSERT`; скрипт: `./scripts/load-fixtures.sh reaction_type.sql` / полная загрузка.
## Frontend
- Загрузка каталога: `GET /api/reactions/catalog` через `reactionCatalogCache.ts` (структура `recent` + `tabs`).
- Компонент **`ReactionStrip`**: ряд «иконка + count» с **hover-popover** и ленивой загрузкой **`GET /api/reactions/actors`**; кнопка открытия пикера — **`IconButton` + `Smile` (lucide)**; пикер с блоком **Недавние**, боковой навигацией **«Коллекции»** и сеткой по категориям. Вёрстка и соглашения: **`docs/frontend/ui-conventions.md`**. Код: публичный импорт [`frontend/src/components/reactions/ReactionStrip.tsx`](/frontend/src/components/reactions/ReactionStrip.tsx), модули в [`frontend/src/components/reactions/reactionStrip/`](/frontend/src/components/reactions/reactionStrip/).
- Точки встраивания: `FeedCard` (реакции на карточку и на комментарии в раскрываемом **прокручиваемом** списке), `MovieCardDetailPage`.

## Tests
- `backend/src/tests/api/test_reactions_asset_route.py` — ключи объекта для прокси, ответ без RustFS (**503**), успешный байтовый поток с мокнутым GetObject (**200**).
- `backend/src/tests/api/test_reactions_routes.py` — каталог, auth, вкладки, недавние после POST, актёры, toggle, замена, неактивный тип, несуществующая цель, реакция на комментарий.
- `backend/src/tests/api/test_cards_routes.py` — обновлён под поле `reactions` и обязательный auth на чтение комментариев.

## References
- `.cursor/features/movie-card-custom-reactions/feature.md`
- `.cursor/active/movie-card-custom-reactions/plan.md`
