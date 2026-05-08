# Result: movie-card-favorites

## Сделано

- Бэкенд: избранное на уровне `movie_card`, публичные поля в ответах, ограничение PATCH владельцем, тесты.
- Документация: `docs/features/movie-card-favorites.md`, артефакты в `.cursor/features` / `.cursor/active`.

## Не сделано

- Фронтенд: компонент сердечка, интеграция в `FeedCard` / `MovieCardDetailPage` / сетку профиля, полоса «Любимое».

## Проверка (ожидается локально / в Docker)

- `make migrate` затем `make backend-test`.

## Изменённые файлы (основные)

См. перечень в `docs/features/movie-card-favorites.md` (раздел «Сервисы и схемы» и «Тесты»).
