# Каталог: общая страница тайтла и оценки сообщества

## Зачем
Пользователь находит тайтл в поиске (`/search` → `/films/:id`). Даже без своей карточки нужно видеть **описание из каталога** и **кто уже оценил** фильм в Filmony, с возможностью открыть чужую карточку или профиль.

## Поведение
- **Описание:** `short_description` и полное `description` с кнопкой разворота длинного текста.
- **Оценки:** список карточек с аватаром, именем, ссылкой на карточку `/cards/:id`, строкой «оценка · компания · настроение», раскрываемой **заметкой о просмотре** и хеш-тегами.
- **Догрузка:** кнопка «Показать ещё», если API вернул `next_cursor`.

## API
`GET /api/films/{film_id}/community-cards?cursor=&limit=` (по умолчанию `limit=20`, макс. 50). Ответ: `items[]` с полем `author` (как у комментариев), `rating`, `company`, `mood_before`, `mood_after`, `watch_note`, `custom_tags`, `updated_at`, `is_favorite`, `next_cursor`.

## Проверка
```bash
make backend-test-one target=src/tests/api/test_film_community_routes.py
cd frontend && npm run lint && npm run build
```
