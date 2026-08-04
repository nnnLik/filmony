---
name: note-spoiler-update
overview: "Подниму лимит заметок карточек с 500 до 1000 и добавлю спойлеры как новый token-based формат для заметок, комментариев и постов. Рекомендую не вводить отдельный rich-text слой: это сохранит текущую архитектуру plain text + токены и позволит переиспользовать рендеринг и валидацию."
todos:
  - id: audit-limits
    content: Синхронизировать лимит заметок 500→1000 во всех backend/frontend точках валидации и UI-константах.
    status: completed
  - id: design-spoiler-token
    content: Зафиксировать формат spoiler token и алгоритм wrap/unwrap для выделенного текста.
    status: completed
  - id: wire-rendering
    content: Планом протянуть рендер скрытого/раскрытого спойлера через общие текстовые компоненты и composer-экраны.
    status: completed
  - id: cover-tests
    content: Добавить/обновить тесты на лимит, токенизацию, рендер и сценарий выделение→спойлер.
    status: completed
  - id: document-work
    content: После реализации оформить результат в feature docs и рабочих артефактах по workflow.
    status: completed
isProject: false
---

# План: лимит заметок и спойлеры

## Цель
- Увеличить лимит текста для заметок карточек с `500` до `1000`.
- Добавить спойлерные блоки, которые скрывают текст до нажатия, и сделать их доступными в заметках карточек, комментариях и постах.
- Сохранить текущую модель plain text + токены, чтобы не перестраивать весь редактор.

## Рекомендуемый подход
- Ввести новый inline token для спойлера в той же системе, где уже живут реакции, упоминания и карточные ссылки.
- Алгоритм для выделенного текста: если есть выделение, оборачивать его в spoiler-маркеры; если выделения нет, вставлять парную заготовку и ставить курсор внутрь; если текст уже обёрнут, уметь снимать спойлер.
- Для рендера отображать спойлер как скрытый блок/плашку, раскрываемый по клику.

## Что нужно изменить
- Обновить ограничения и нормализацию заметок в backend:
  - `[backend/src/api/cards/schemas.py](backend/src/api/cards/schemas.py)`
  - `[backend/src/api/profile/schemas.py](backend/src/api/profile/schemas.py)`
  - `[backend/src/api/watchlist/schemas.py](backend/src/api/watchlist/schemas.py)`
  - `[backend/src/services/cards/create_user_card.py](backend/src/services/cards/create_user_card.py)`
  - `[backend/src/services/cards/update_user_card.py](backend/src/services/cards/update_user_card.py)`
  - `[backend/src/services/cards/create_planned_user_card.py](backend/src/services/cards/create_planned_user_card.py)`
  - `[backend/src/services/watchlist/create_watchlist_entry.py](backend/src/services/watchlist/create_watchlist_entry.py)`
  - `[backend/src/services/watchlist/update_watchlist_entry.py](backend/src/services/watchlist/update_watchlist_entry.py)`
- Протянуть новый spoiler token через frontend:
  - `[frontend/src/lib/commentReactionTokens.ts](frontend/src/lib/commentReactionTokens.ts)` или тонкий соседний helper для spoiler-операций
  - `[frontend/src/components/comments/CommentBodyWithReactionTokens.tsx](frontend/src/components/comments/CommentBodyWithReactionTokens.tsx)`
  - compose/entrypoint-сцены для комментариев, постов и заметок: `FeedComposeSheet`, `FeedCard`, `FeedPostCard`, `FeedPostDetailPage`, `MovieCardDetailPage`, `CreateCardPage`, `EditMovieCardPage`, `ShareMovieCardPage`
- Добавить проверки/тесты для:
  - нового лимита `1000`
  - валидации/нормализации спойлеров
  - рендера скрытого/раскрытого состояния
  - логики выделение → обёртка → снятие обёртки

## Варианты реализации
- **Вариант A, рекомендованный:** token-based spoiler поверх текущего plain-text редактора. Меньше рисков, переиспользует текущие компоненты, проще тестировать.
- **Вариант B:** markdown-подобный синтаксис для спойлеров. Проще для ручного ввода, но потребует шире менять парсинг и валидацию.
- **Вариант C:** полноценный rich-text editor. Даёт самый гибкий UX, но это уже крупный рефакторинг и не нужен для текущего объёма.

## Критерии готовности
- Заметки карточек принимают до `1000` символов и одинаково ограничены на backend/frontend.
- Спойлеры работают в заметках, комментариях и постах.
- Выделенный текст можно пометить спойлером через единый сценарий в composer-UI.
- Есть тесты на лимит, рендер и токенизацию, без регрессий для существующих реакций/упоминаний/ссылок.
