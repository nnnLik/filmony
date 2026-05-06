# Implementation Plan

## Feature
- Slug: `movie-card-custom-reactions`
- Source spec: `.cursor/features/movie-card-custom-reactions/feature.md`

## Goal
- Каталог кастомных картинок-реакций и возможность ставить/снимать их на **карточки** и **комментарии** (свои и чужие), без unicode-emoji по умолчанию.

## Step-by-Step Plan
1. Спроектировать модели: `ReactionType` (каталог), `UserReaction` (полиморфная пара target_type + target_id или две таблицы).
2. Миграции Alembic + seed минимального каталога (или документированный SQL).
3. Сервисы: `ListReactionCatalogService`, `SetOrToggleUserReactionService`, `ListReactionsForTargetService` (или агрегация в существующих list/detail).
4. API routes + схемы; встраивание агрегатов в ответы карточки/комментариев при необходимости.
5. `pytest`: каталог, toggle, уникальность, невалидный тип, чужая карточка разрешена.
6. Frontend: загрузка каталога, пикер, отображение счётчиков на `FeedCard` / detail / комментарии.
7. Обновить `docs/features/movie-card-custom-reactions.md`, `result.md`, action-log.

## Verification Plan
- `make backend-test-one target=...` для новых тестов (Docker).
- Ручной smoke: две учётки, реакция на карточку и на комментарий видна со второй стороны.
