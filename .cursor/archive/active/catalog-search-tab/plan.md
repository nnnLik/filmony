# План реализации: catalog-search-tab

Копия структуры из корневого плана репозитория; исполнение — по слайсам S1→S2→S3→S4.

## SLICE_MATRIX

| Slice | Содержание |
|-------|------------|
| S1 | `GET /api/search` + сервисы + тесты |
| S2 | `GET /api/search/suggestions` + дедуп + тесты |
| S3 | Фронт: `SearchPage`, `BottomNav`, routes, API (в т.ч. выдача `cards` → `/cards/:id`, fallback `films`) |
| S4 | `docs/features/catalog-search-tab.md`, `result.md`, action-log |

## AGENT_QUEUE

1. Спека — `feature.md` (этот репозиторий).
2. S1 backend-dev.
3. S2 backend-dev.
4. S3 frontend-dev.
5. Документация + verification.
