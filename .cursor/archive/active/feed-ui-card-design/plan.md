# Implementation Plan

## Feature
- Slug: `feed-ui-card-design`
- Source spec: `.cursor/features/feed-ui-card-design/feature.md`

## Goal
- Зафиксировать и внедрить UX/UI карточки ленты с preview комментариев и inline-комментированием.

## Step-by-Step Plan
1. Провести аудит текущих компонентов карточек и комментариев во frontend, определить переиспользуемые блоки.
2. Спроектировать пропсы и контракт `FeedCard` (данные + callbacks на действия).
3. Реализовать визуальные блоки карточки: постер, title, rating, системные теги (визуальные), кастомные теги (лимит + `+N`).
4. Реализовать секцию preview комментариев (до 2 шт.) и CTA перехода в detail.
5. Реализовать inline-comment composer в карточке с локальным optimistic обновлением.
6. Добавить состояния loading/error для карточки и отправки комментария.
7. Обновить/добавить frontend тесты на ключевые интеракции карточки.

## Files Expected To Change
- `frontend/src/pages/*` (страница ленты, если отсутствует - создать)
- `frontend/src/components/*` (новый/обновленный компонент карточки)
- `frontend/src/api/cardApi.ts` (при необходимости уточнить контракты данных для ленты)
- `frontend/src/styles/*` (если есть локальные стили компонентов)

## Verification Plan
- `cd frontend && npm run lint`
- `cd frontend && npm run test` (или профильный тест-команд для измененных тестов)
- Ручной smoke:
  - карточка отображает постер/title/rating;
  - системные теги в визуальном формате;
  - кастомные теги ограничены и показывают `+N`;
  - inline комментарий отправляется и появляется в preview;
  - `Все комментарии` ведет в detail страницы карточки.
