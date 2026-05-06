# Соглашения по UI фронтенда (лента, реакции, иконки)

Документ для разработчиков и ИИ-агентов: что уже подключено в проекте и как этим пользоваться, чтобы не дублировать решения и не ломать вёрстку.

## Зависимости

| Пакет | Назначение |
|--------|-------------|
| `@telegram-apps/telegram-ui` | Базовый UI (кнопки, секции, **IconButton**, Avatar, …). |
| `lucide-react` | Контурные иконки (SVG), когда в TGUI нет нужного символа в экспорте пакета. |

Установка уже в `frontend/package.json`. Новые иконки — по возможности из **lucide** с единым `strokeWidth` (1.75–2), не смешивать с произвольными inline-SVG без причины.

## Кнопка «добавить реакцию» (`ReactionStrip`)

- Триггер каталога реакций: **`IconButton`** из `@telegram-apps/telegram-ui` (`mode="gray"`, `size="s"`) + иконка **`Smile`** из `lucide-react`.
- **Центрирование:** у `IconButton` через Tailwind задаются `flex! items-center! justify-center! p-0! leading-none! relative z-0`, у `Smile` — `block shrink-0 relative z-1` и фиксированный `size-*`. Так иконка не уезжает в угол: внутри TGUI `Tappable` первым ребёнком идёт слой ripple, inline-SVG иначе выравнивается по baseline.
- Размеры: **compact** (лента / узкая полоса) — кнопка 22×22, иконка 15px; обычный режим — 36×36 (`h-9 w-9`), иконка 18px.

Файлы (импорт из приложения — по-прежнему из **`components/reactions/ReactionStrip`**):

- [`frontend/src/components/reactions/ReactionStrip.tsx`](../../frontend/src/components/reactions/ReactionStrip.tsx) — реэкспорт `ReactionStrip` / `ReactionStripProps`.
- [`frontend/src/components/reactions/reactionStrip/`](../../frontend/src/components/reactions/reactionStrip/) — реализация: `ReactionStrip.tsx`, `ReactionStripPopover.tsx`, `CountPill.tsx`, `ReactionThumb.tsx`, `usePopoverPosition.ts`, `constants.ts`, `displayActorName.ts`.

## Лента: карточка (`FeedCard`)

- Нижний блок: **одна строка** — слева `ReactionStrip` с `compact`, справа подпись **«Комментарии»**, счётчик, стрелка раскрытия; между блоками лёгкий `border-l`.
- Комментарии и поле ввода **скрыты по умолчанию**; раскрытие по стрелке; после успешной отправки комментария блок раскрывается программно.
- Карточка уплотнена: `gap-2`, `p-2.5`, меньшие отступы у превью и поля ввода.

Файлы:

- [`frontend/src/components/feed/FeedCard.tsx`](../../frontend/src/components/feed/FeedCard.tsx) — разметка и состояние карточки.
- [`frontend/src/components/feed/feedCardUtils.ts`](../../frontend/src/components/feed/feedCardUtils.ts) — подписи enum’ов, палитра оценки, форматирование.
- [`frontend/src/components/feed/FeedCardIcons.tsx`](../../frontend/src/components/feed/FeedCardIcons.tsx) — локальные SVG-иконки (отправка, шеврон).

## Типы для Telegram UI

Расширения амбиентного модуля — [`frontend/src/types/telegram-apps-telegram-ui.d.ts`](../../frontend/src/types/telegram-apps-telegram-ui.d.ts) (в т.ч. `IconButton`, если IDE не подхватывает полный `dist` пакета).

## Связанная продуктовая документация

- Реакции API и поведение: [`docs/features/movie-card-custom-reactions.md`](../features/movie-card-custom-reactions.md).

## Проверка после правок

```bash
cd frontend && npm run build && npm run lint
```
