# Movie card custom reactions

## Goal
Реакции на **карточки фильмов** и **комментарии** только из **каталога кастомных картинок** в БД. Стандартные emoji-мессенджера как дефолтный набор не используются.

## Data model
- **`reaction_type`**: `id`, `created_at`, `label` (опционально), `image_url` (строка URL или стабильный путь CDN), `sort_order`, `is_active`.
- **`user_reaction`**: `user_id` → `user`, `reaction_type_id` → `reaction_type` (RESTRICT при удалении типа), `target_kind` (`movie_card` | `movie_card_comment`), `target_id`. Уникальность: одна строка на пару пользователь + цель.

## Behaviour (MVP)
- Одна реакция пользователя на цель. Повторный `POST` с тем же `reaction_type_id` **снимает** реакцию (toggle).
- Выбор другого типа из каталога **заменяет** строку (`reaction_type_id` обновляется).
- Self-react разрешён (флаг в `SetOrToggleUserReactionService`).
- Уведомления в Telegram **вне scope**; хук возможен через комментарий в сервисе после commit.

## API
### `GET /api/reactions/catalog`
Требует аутентификацию. Ответ: `{ items: [{ id, label, image_url }] }` только с `is_active = true`, сортировка по `sort_order`, `id`.

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

Ошибки: неизвестная/выключенная реакция — **422**, цель не найдена — **404**, некорректный `target_kind` — **422**.

### Вложенные поля в существующие ответы
Поле **`reactions`** того же вида добавлено к:
- `GET /api/cards/feed` (карточка и каждый элемент `comments_preview`);
- `GET /api/cards/{id}`;
- `GET /api/cards/{id}/comments` и replies.

Агрегаты считаются батчем в **`GetReactionSummariesForTargetsService`** (без N+1 на число типов или комментариев на странице).

**Требование к клиенту:** списки комментариев и replies вызываются **с авторизованной сессией** (как лента).

## Fixtures
- После миграций: `fixtures/reaction_type.sql` или ручные `INSERT`; скрипт: `./scripts/load-fixtures.sh reaction_type.sql` / полная загрузка.

## Frontend
- Загрузка каталога: `GET /api/reactions/catalog` через `reactionCatalogCache.ts`.
- Компонент `ReactionStrip`: ряд «иконка + count», клик по счётчику повторяет toggle; кнопка «+» открывает пикер (нижняя панель).
- Точки встраивания: `FeedCard`, `MovieCardDetailPage`.

## Tests
- `backend/src/tests/api/test_reactions_routes.py` — каталог, auth, toggle, замена, неактивный тип, несуществующая цель, реакция на комментарий.
- `backend/src/tests/api/test_cards_routes.py` — обновлён под поле `reactions` и обязательный auth на чтение комментариев.

## References
- `.cursor/features/movie-card-custom-reactions/feature.md`
- `.cursor/active/movie-card-custom-reactions/plan.md`
