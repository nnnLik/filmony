# Global Feed: сортировка карточек по updated_at

**Статус:** готово.

## Проблема
Глобальная лента (`GET /api/feed/global`) сортировала карточки по `UserCard.created_at`. После создания «позже»/planned-карточки и последующей активности (редактирование, апгрейд в оценённую) `updated_at` обновлялся, но карточка оставалась ниже в ленте. Социальная лента подписок уже использовала `updated_at` (см. [`feed-ordering-updated-at`](feed-ordering-updated-at.md)).

## Что изменилось
- В `ListGlobalFeedService` для ветки карточек `sort_at` = `UserCard.updated_at` (ранее `created_at`).
- Посты по-прежнему сортируются по `FeedPost.created_at`.
- Смешанная вкладка **Всё** (`kind=all`) сравнивает карточки и посты по их respective `sort_at`.

## Поведение при апгрейде planned → rated
Путь `CreateUserCardService._finalize_upgraded_planned` обновляет поля карточки и делает `commit`. Колонка `UserCard.updated_at` имеет `onupdate=func.now()`, поэтому апгрейд «позже» в оценённую карточку **автоматически** поднимает карточку в глобальной ленте (при условии, что новый `updated_at` новее соседних элементов). Отдельный явный `entity.updated_at = …` в сервисе не требуется.

## Проверка
```bash
make backend-test-one target=src/tests/api/test_global_feed_routes.py
```
Ожидаемый результат: **9 passed**.

Ключевые тесты:
- `test_global_feed_cards_sort_by_updated_at` — `kind=cards`, PATCH поднимает старую карточку выше.
- `test_global_feed_all_resurfaces_updated_card_above_newer_post` — `kind=all`, обновлённая карточка выше более нового поста.

Связанный регресс planned→rated для ленты подписок:
```bash
make backend-test-one target=src/tests/api/test_cards_routes.py::test_movie_card_feed_promotes_converted_planned_card
```

## Ограничения
- Просмотр карточки (GET) **не** меняет `updated_at`.
- Посты не переходят на `updated_at`.
- Старые keyset-курсоры могут дать лёгкую несогласованность, если карточка обновилась во время пагинации.

## Файлы
- `backend/src/services/feed/list_global_feed.py`
- `backend/src/tests/api/test_global_feed_routes.py`
