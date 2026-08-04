---
name: Unified comments design doc
overview: "Канонический проектный документ уже лежит в [brainstorming/unified-comments-model-design.md](brainstorming/unified-comments-model-design.md): целевая «идеальная» модель (логически единый комментарий, физически две таблицы — подход A), паритет полей/API включая `image_url` для постов, общее ядро валидации и пофазная миграция. После вашего подтверждения имеет смысл лишь слегка дополнить MD (диаграмма, трассировка требований, non-goals) и затем вести реализацию по фазам из раздела 8 документа."
todos:
  - id: review-md
    content: Прочитать и утвердить/править brainstorming/unified-comments-model-design.md (при необходимости — mermaid, трассировка, non-goals, инвентарь файлов)
    status: pending
  - id: phase1-backend
    content: "После утверждения: фаза 1 из §8 документа — Alembic image_url, модель, is_safe ключ, create/list/schemas, upload, pytest"
    status: pending
  - id: phase3-frontend
    content: "После фазы 1: фаза 3 — типы, API, UI комментариев к посту (паритет с карточкой), lint/build"
    status: pending
isProject: false
---

# План: единая модель комментариев (документ + дальнейшие шаги)

## Где лежит план

Весь проработанный дизайн и план миграции уже собраны в **[brainstorming/unified-comments-model-design.md](brainstorming/unified-comments-model-design.md)** (разделы 1–11): текущее состояние vs цель, требования, сравнение подходов A/B/C с **рекомендацией A** (две таблицы + общее ядро), целевая схема данных (`feed_post_comment.image_url`), медиа-префикс `user_media/feed_post_comments/`, единые контракты API, декомпозиция `services/comments/`, фазы миграции 0–5, риски и DoD.

Это и есть отдельный MD «пока без кода» — отдельный репозиторный артефакт для согласования.

## Соответствие вашим требованиям (проверка по документу)

| Ожидание | Отражение в MD |
|----------|-----------------|
| Одинаковые правила тела (текст **или** картинка, токены/упоминания) | §2.1, §5.3, §6.1, §7 |
| Картинка у комментария к посту наравне с карточкой | §1.3, §5.1–5.2, фаза 1 §8 |
| Дерево ответов и тот же паттерн списка | §2.1 п.4, §1.1–1.2 |
| «В ленту» как исключение, не ломающее модель | §2.3 |
| Не лезть в одну полиморфную таблицу без нужды | §3–4 |
| Тесты и Docker | §2.2, §8 фаза 1, §10 |

## Рекомендуемые точечные улучшения документа (после вашего «ок» к плану)

Не меняя выбранный подход A, можно усилить MD для «идеальности» описания:

1. **Mermaid-схема** (логическая сущность `Comment` vs две физические таблицы + общие модули `comment_reaction_tokens`, нормализатор `image_url`, реакции по `target_kind`).
2. **Таблица трассировки**: строка = требование из §2.1 → файлы/слои, которые его гарантируют (backend/frontend/tests).
3. **Explicit non-goals**: например «не объединяем таблицы в релизе N», «не меняем id-space реакций» — чтобы не раздували scope.
4. **Инвентарь затронутых поверхностей** для фазы 1: [backend/src/models/feed_post_comment.py](backend/src/models/feed_post_comment.py), [backend/src/services/feed_posts/create_feed_post_comment.py](backend/src/services/feed_posts/create_feed_post_comment.py), [backend/src/api/feed_posts/schemas.py](backend/src/api/feed_posts/schemas.py), [backend/src/utils/feed_post_media_key.py](backend/src/utils/feed_post_media_key.py), гидратация preview (например [backend/src/api/cards/feed_post_feed_mapping.py](backend/src/api/cards/feed_post_feed_mapping.py)), фронт типы/API страницы поста — как чеклист к §8.

## Что делать после утверждения этого плана

1. **Документ**: применить пункты «улучшения» выше прямо в `brainstorming/unified-comments-model-design.md` (или оставить как есть, если устраивает текущая версия).
2. **Реализация**: идти строго по **§8 фазы 1 → 3** документа (Alembic → сервисы/API → pytest → фронт); фазы 4–5 по необходимости.
3. **Процесс репозитория**: при полноценной фиче — отдельный `docs/features/…` и лог по workflow проекта (если включите delivery workflow).

## Однозначная формулировка «идеальной модели» (как в документе)

**Идеально для Filmony:** один доменный комментарий по правилам и API, **две таблицы** как два корня (`movie_card` / `feed_post`), общее ядро валидации и медиа, раздельные `target_kind` для реакций и раздельные Telegram-цепочки до явного рефакторинга.
