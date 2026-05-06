# План разбиения `ReactionStrip` и `FeedCard` (к выполнению в Agent mode)

Среда в **Plan mode** не позволяет менять `.ts`/`.tsx`. Ниже — точная схема для реализации в Agent mode одним проходом.

## ReactionStrip → `components/reactions/reactionStrip/`

| Файл | Содержимое |
|------|------------|
| `constants.ts` | `EMPTY`, `POPOVER_*`, `SIDE_PAD`, `PICK_*` |
| `displayActorName.ts` | `displayActorName` |
| `ReactionThumb.tsx` | компонент превью картинки |
| `usePopoverPosition.ts` | хук позиционирования портала |
| `ReactionPickerBody.tsx` | разметка диалога пикера (ошибка/загрузка, nav «Коллекции», недавние, сетка) — пропсы: `catalog`, `catalogError`, `busy`, `effectiveTabSlug`, `setActiveTabSlug`, `activeTab`, `gridItems`, `recentItems`, `myReactionIds`, `countsById`, `compact`, `apply` |
| `CountPill.tsx` | кнопка-счётчик + hover tooltip актёров |
| `ReactionStrip.tsx` | состояние, `apply`, портал (backdrop + оболочка + стрелка + `ReactionPickerBody`), полоска `CountPill` + `IconButton` |

Публичный API: корневой [`frontend/src/components/reactions/ReactionStrip.tsx`](../../frontend/src/components/reactions/ReactionStrip.tsx) только реэкспорт:

```ts
export { ReactionStrip, type ReactionStripProps } from './reactionStrip/ReactionStrip'
```

Импорты в `FeedCard` / `MovieCardDetailPage` **не меняются**.

## FeedCard → `components/feed/`

| Файл | Содержимое |
|------|------------|
| `feedCardLabels.ts` | `COMPANY_SHORT`, `MOOD_BEFORE_SHORT`, `MOOD_AFTER_SHORT`, `ratingPalette`, `formatRating`, `ratingDashOffset` |
| `feedCardAuthors.ts` | `authorLabel`, `formatCommentTime`, `commentAuthorDisplay`, `snippetPreview` |
| `FeedCardIcons.tsx` | `IconSend`, `IconChevronDown` |
| `FeedCardPosterBlock.tsx` | блок постера + градиент + `ReactionStrip` на карточке + кольцо рейтинга (пропсы: `card`, `cardHref`, `cardReaction`, `setCardReaction`, `stopCardNav`) |
| `FeedCardCommentsBlock.tsx` | раскрываемый блок превью комментариев + `ReactionStrip` на комментариях + поле ввода (пропсы/state колбэки из родителя) |
| `FeedCard.tsx` | оркестратор (`useState`, `useCallback`, сборка секций) |

## Документация — обновить ссылки на «основной» файл

После рефакторинга в финальных доках указать:

- **Главная точка входа** реакций: [`frontend/src/components/reactions/ReactionStrip.tsx`](../../frontend/src/components/reactions/ReactionStrip.tsx) (реэкспорт).
- **Реализация / сопровождение пикера**: [`frontend/src/components/reactions/reactionStrip/`](../../frontend/src/components/reactions/reactionStrip/) (перечислить ключевые файлы в одном предложении).
- **Карточка ленты**: [`frontend/src/components/feed/FeedCard.tsx`](../../frontend/src/components/feed/FeedCard.tsx) + при необходимости ссылка на `feed/FeedCardPosterBlock.tsx`, `feed/FeedCardCommentsBlock.tsx`.

Файлы для правки ссылок:

- [`docs/frontend/ui-conventions.md`](../frontend/ui-conventions.md)
- [`docs/engineering/project-structure-and-style.md`](project-structure-and-style.md)
- [`docs/features/movie-card-custom-reactions.md`](../features/movie-card-custom-reactions.md)
- [`docs/features/feed-ui-card-design.md`](../features/feed-ui-card-design.md)
- [`.cursor/tech.md`](../../.cursor/tech.md) — при желании одна строка про модуль `reactionStrip/`

Проверка: `cd frontend && npm run lint && npm run build`.
