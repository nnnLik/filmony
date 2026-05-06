# Feed Recommendation Engine

## Goal
- Определить и зафиксировать реализационную логику выдачи ленты с балансом релевантности и разнообразия.

## Каноничность и наследие (007 / 008)

- **Единый документ по ленте и смешиванию источников** в продукте сейчас — этот файл и спека `.cursor/features/feed-recommendation-engine/feature.md`.
- **`.cursor/features/007-feed-friends-and-stranger-inserts.md`** — историческая спека: «друзья» и отдельный `GET /api/feed` заменены концепцией **подписки / подписчики** и текущим контуром карточек (например `GET /api/cards/feed`); «вкидки» соответствуют каналу **`discovery`** и при необходимости сортировкам в этой спеке.
- **`.cursor/features/008-doppelganger-recommendations.md`** — не удаляется: описывает **будущее усиление** похожести пользователей (вектора, соседи, Redis). В терминах ленты это ложится на **`personal_affinity`** и точечный **discovery**, а не на отдельный параллельный продуктовый документ. Когда двойники будут в коде — расширять **этот** документ разделом про источник сигнала, а не плодить вторую «ленточную» спеку.

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
