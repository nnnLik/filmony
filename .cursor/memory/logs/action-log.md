# Action Log

Каждое изменение хранится в отдельном файле в этой директории.

## Правило хранения
- Один файл = одно действие.
- Формат имени: `YYYY-MM-DDTHHMMSSZ-<feature-slug>-<action-type>.md`.
- Пример: `2026-05-06T053800Z-movie-card-comments-code.md`.

## Формат записи (внутри файла)
- Timestamp
- Feature slug
- Action type: `plan | code | test | docs | refactor | decision`
- Summary
- Files
- Verification
- Links (опционально)

## Примечание
- Агрегированные файлы логов больше не используются.
