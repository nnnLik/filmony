# Feed Recommendation Engine

## Goal
- Определить и зафиксировать реализационную логику выдачи ленты с балансом релевантности и разнообразия.

## Concrete Requirements
- Источники кандидатов: `subscriptions`, `subscribers`, `personal_affinity`, `discovery`.
- Discovery-контент дозируется и обязательно присутствует в выдаче.
- Порядок стабильный при одинаковом cursor.
- Дедупликация карточек внутри сессии листания обязательна.
- Cursor-based API с предсказуемой пагинацией.

## Success Criteria
- p95 latency feed endpoint в целевом SLA.
- Стабильная детерминированная выдача на одинаковом cursor.
- Соблюдение доли discovery.
- Отсутствие "пустых" лент у пользователей с небольшим social graph.

## MVP
- Простая кандидатогенерация (subscriptions/subscribers/discovery pool).
- Линейный scoring: свежесть + social proximity + совпадение интересов.
- Детерминированное смешивание по квотам источников.
- Cursor-pagination и защита от дублей.
- Базовые метрики качества и производительности.

## Next Implementation Step
- Реализовать backend сервис и feed endpoint по шагам из `.cursor/active/feed-recommendation-engine/plan.md`.
