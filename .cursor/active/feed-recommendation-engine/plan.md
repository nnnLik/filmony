# Implementation Plan

## Feature
- Slug: `feed-recommendation-engine`
- Source spec: `.cursor/features/feed-recommendation-engine/feature.md`

## Goal
- Реализовать стабильную и быструю выдачу ленты с контролируемым смешиванием social и discovery контента.

## Step-by-Step Plan
1. Описать backend контракт feed endpoint (query params, cursor, response schema, source diagnostics для отладки).
2. Реализовать сервис-класс генерации кандидатов по источникам: подписки, подписчики, персональные сигналы, discovery.
3. Реализовать scoring + deterministic mixing с конфигурируемыми квотами по источникам.
4. Реализовать cursor pagination и дедупликацию на уровне выдачи.
5. Добавить защитные правила: анти-спам, ограничение повторов автора/фильма.
6. Добавить тесты сервиса и API: happy path, курсорная стабильность, доля discovery, empty graph.
7. Добавить метрики/логирование для latency, source mix, duplicate rate.

## Files Expected To Change
- `backend/src/api/*` (новый feed endpoint и схемы)
- `backend/src/services/*` (новый feed service)
- `backend/src/tests/api/*`
- `backend/src/tests/services/*`
- `backend/src/models/*` (если потребуются новые сущности/индексы/материализация)

## Verification Plan
- `make backend-test-one target=src/tests/api/...` (новые тесты feed API)
- `make backend-test-one target=src/tests/services/...` (новые тесты feed service)
- `make backend-test` (минимум на финальном этапе фичи)
- Ручная верификация:
  - стабильность выдачи на одинаковом cursor;
  - наличие discovery в заданной доле;
  - отсутствие дублей в пределах сессии листания.
