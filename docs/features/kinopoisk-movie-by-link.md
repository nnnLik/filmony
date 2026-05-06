# Kinopoisk movie by link

## Summary

Фича **закрыта на уровне MVP**: пользователь вставляет ссылку на фильм с `kinopoisk.ru`, бэкенд извлекает id, подтягивает метаданные через Kinopoisk API client, upsert в таблицу `films`, отдаёт клиенту для создания карточки.

## Реализовано

- **Парсинг URL**: `backend/src/services/kinopoisk/parse_url.py` — путь вида `/film/{id}` на хосте `*.kinopoisk.ru`.
- **Резолв**: `ResolveKinopoiskFilmService` — при существующем `kinopoisk_id` обновляет поля фильма из API; иначе создаёт строку.
- **API**: `POST /api/films/resolve` с телом `{ "url": "..." }` → `FilmResponse`; ошибки парсинга `422`, сбой внешнего API `502`.
- **Клиент**: `GET /api/films/{film_id}`.
- **Frontend**: `resolveFilmByKinopoiskUrl` в `frontend/src/api/cardApi.ts`, использование в потоке создания карточки (`CreateCardPage`).

Идемпотентность по смыслу: один `kinopoisk_id` — одна строка в БД (уникальность на уровне модели).

## Optional enhancements (не обязательны для «закрытия» фичи)

- Поддержка **дополнительных форматов** ссылок (мобильные редиректы, query-параметры, серии/слуги — только если продукт требует).
- **Асинхронный** resolve через Celery + polling, если внешний API станет нестабильным или таймауты HTTP начнут бить UX.
- Сохранение **сырого JSON** метаданных в отдельном поле для будущих фильтров (cast, страны и т.д.).

## References

- Историческая спека: `.cursor/features/004-kinopoisk-movie-by-link.md`
- Создание карточки: `docs/features/movie-card-create-flow.md`
