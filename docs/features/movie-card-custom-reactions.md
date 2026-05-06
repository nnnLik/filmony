# Movie card custom reactions

## Goal
Реакции на **карточки фильмов** и **комментарии** только из **каталога кастомных картинок** в БД. Стандартные emoji-мессенджера как дефолтный набор не используются.

## Data model
- **`reaction_type`**: `id`, `created_at`, `label` (опционально), `category_slug` (вкладка пикера), `asset_key` (S3-ключ относительно публичного base, например `reactions/pepe/foo.png`), `image_url` (fallback если base или asset пустые), `sort_order`, `is_active`.
- **`user_reaction`**: `user_id` → `user`, `reaction_type_id` → `reaction_type` (RESTRICT при удалении типа), `target_kind` (`movie_card` | `movie_card_comment`), `target_id`. Уникальность: одна строка на пару пользователь + цель.
- **`user_recent_reaction`**: последние выбранные реакции пользователя (`user_id`, `reaction_type_id`, `last_used_at`, unique на пару). Обновляется при успешной установке/смене реакции (не при toggle-off).

## Behaviour (MVP)
- Одна реакция пользователя на цель. Повторный `POST` с тем же `reaction_type_id` **снимает** реакцию (toggle).
- Выбор другого типа из каталога **заменяет** строку (`reaction_type_id` обновляется).
- Self-react разрешён (флаг в `SetOrToggleUserReactionService`).
- Уведомления в Telegram **вне scope**; хук возможен через комментарий в сервисе после commit.

## CDN / RustFS (dev)
- В `compose.yml` сервис **`filmony-rustfs`** (образ `rustfs/rustfs:latest`), том `filmony-rustfs-data`, хост-порты **7900→9000**, **7901→9001** (консоль при необходимости).
- Для прямых публичных URL (без прокси) с path-style клиент собирает: `{REACTION_MEDIA_PUBLIC_BASE_URL}/{asset_key}` (без двойных слешей). Пример base: `http://127.0.0.1:7900/filmony-reactions`. Mini App без LAN к этому адресу: либо **прокси бэкенда**, либо отдельный HTTPS-домен к RustFS на том же origin, что и API.
- С **прокси** (переменная `RUSTFS_INTERNAL_BASE_URL` на backend, см. `compose.yml` для `filmony-backend`): в ответах API при наличии `asset_key` отдаются пути **`/api/reactions/asset/<asset_key>`**; бэкенд забирает объект из контейнерного RustFS (`http://filmony-rustfs:9000/…`). Если внутренний URL не задан (например `pytest`), сохраняется режим только с **`REACTION_MEDIA_PUBLIC_BASE_URL`**.
- Сидеры в [`fixtures/reaction_type.sql`](/fixtures/reaction_type.sql) задают **`asset_key`** под объекты, которые загружает `make sync-reactions-rustfs` из `emoji/` (`reactions/<category_slug>/<file>`).
- Политику **анонимного чтения только префикса** `reactions/*` нужно настроить в bucket (через консоль RustFS/`mc`/policy по вашей среде).
- Загрузка файлов из репозитория: `scripts/sync_reactions_to_rustfs.py` (boto3, `endpoint_url` + `signature_version='s3v4'`), переменные — см. `vars/.env.example` (`RUSTFS_*`).
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
    "my_reaction_type_id": 1
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
- Сначала залить объекты в RustFS: `make sync-reactions-rustfs` (ключи вида `reactions/<slug>/…` как в сидере).
- После миграций: `fixtures/reaction_type.sql` или ручные `INSERT`; скрипт: `./scripts/load-fixtures.sh reaction_type.sql` / полная загрузка.
## Frontend
- Загрузка каталога: `GET /api/reactions/catalog` через `reactionCatalogCache.ts` (структура `recent` + `tabs`).
- Компонент `ReactionStrip`: ряд «иконка + count» с **hover-popover** и ленивой загрузкой **`GET /api/reactions/actors`**; кнопка открытия пикера — **`IconButton` + `Smile` (lucide)**; пикер с **поиском**, блоком **Недавние** и **вкладками** категорий. Вёрстка и соглашения: **`docs/frontend/ui-conventions.md`**.
- Точки встраивания: `FeedCard`, `MovieCardDetailPage`.

## Tests
- `backend/src/tests/api/test_reactions_routes.py` — каталог, auth, вкладки, недавние после POST, актёры, toggle, замена, неактивный тип, несуществующая цель, реакция на комментарий.
- `backend/src/tests/api/test_cards_routes.py` — обновлён под поле `reactions` и обязательный auth на чтение комментариев.

## References
- `.cursor/features/movie-card-custom-reactions/feature.md`
- `.cursor/active/movie-card-custom-reactions/plan.md`
