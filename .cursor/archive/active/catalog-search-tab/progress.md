# Progress: catalog-search-tab

- Фича завершена: поиск теперь ищет локальные карточки по title/display_title, показывает summary и ведёт на `/cards/:cardId`.
- `films` сохранён как legacy alias для совместимости; поиск пользователей и suggestions оставлены без регрессий.
- Верификация пройдена: `docker compose -f docker-compose.yml exec -T backend pytest -q`, `cd frontend && npm run lint && npm run build`.
