# Редизайн создания карточки, поста и «Позже»

**Статус:** утверждён (Approach 2)  
**Дата:** 2026-07-19

## Проблема и цели

Сейчас создание контента из ленты размазано по двум неочевидным точкам входа («+» ведёт на `/cards/new`, отдельная ручка открывает `FeedComposeSheet`), а карточка проходит четырёхшаговый wizard с разветвлением «Позже» внутри того же потока. Пользователю сложно понять, что он создаёт; обложку часто приходится искать вручную по URL; провайдер каталога смешивается с типом карточки в UI.

**Цели доставки:**

- **≤2 осмысленных тапа** от ленты до понятного выбора «карточка / пост / позже».
- **Одно умное поле** «название или ссылка» с mixed-кандидатами вместо выбора провайдера на первом шаге.
- **Один длинный scroll-форм** после выбора кандидата или ручного ввода — без multi-step wizard.
- **Обложка всегда с превью** и тремя равноправными действиями: Загрузить / Ссылка / Буфер — без охоты за URL в интернете.
- **Архитектура:** `UserCard` остаётся абстрактной сущностью с `display_*` и опциональным `catalog_item_id`; Kinopoisk, RAWG и будущие интеграции — **Sources**, а не типы карточки.
- **Тонкий backend** Sources→Candidates + upload обложки; существующие create card/post/watchlist контракты меняются минимально.

## Non-goals

- **YouTube** и любые новые провайдеры в этой доставке — только задел через контракт Candidate; реализация Source откладывается.
- Переименование `movie_card` / legacy API-имён в коде и БД.
- Объединённый compose «пост + карточка» в одном экране.
- Multi-step wizard для rated-карточки или watchlist.
- Режим «Позже» как ветка внутри scroll-формы оценённой карточки.
- Рефакторинг ленты, сортировки, реакций и прочих систем вне scope создания.
- Изменение семантики дубликата карточки — предупреждение о дубликате **сохраняется** как сейчас.

## UX-решения (зафиксированные A/B)

| Область | Отвергнуто | Принято |
|--------|------------|---------|
| Вход из ленты | Две иконки (+ и ручка) | **Concept A:** одна кнопка «Создать» → action sheet |
| Пункты sheet | Только карточка и пост | **Три строки:** Карточка \| Пост \| Позже (с короткими подзаголовками) |
| Первый экран карточки | Выбор типа (фильм / игра / своё) | **Smart single field** «название или ссылка» |
| Поиск каталога | Отдельные запросы по провайдеру | **Mixed candidates** одним списком (`GET /api/catalog/candidates`) |
| Конфликт «Castlevania» (фильм vs игра) | Автовыбор по `kind_hint` на сервере | **Пользователь выбирает кандидата**; `kind_hint` только для группировки/иконки в UI |
| После pick / manual | Multi-step wizard (4 шага) | **Один длинный scroll-form** |
| Watchlist | Ветка wizard или режим в rated-form | **Отдельная короткая форма** из пункта 3 sheet; не mode на rated scroll |
| Пост | Новый экран compose | **Сохранить `FeedComposeSheet`**; улучшить только ясность входа через sheet |
| Обложка | Только URL или только upload | **Всегда превью + три равные кнопки:** Загрузить / Ссылка / Буфер |
| Upload обложки | Новый протокол | **Как у постов ленты** (`POST /api/cards/covers/upload`, аналог `uploadFeedPostImage`) |
| Аудио / шаринг | В основном scroll-form | **Вторично после успешного create** (как сейчас по смыслу, не блокируют submit) |
| Backend shape | Card types per provider | **Sources → Candidates**; card abstract |

## Архитектура

### Абстрактная карточка (`UserCard`)

Карточка пользователя не «фильмовая» и не «игровая» по типу модели. Отображение и привязка к каталогу:

| Поле | Назначение |
|------|------------|
| `catalog_item_id` | Опциональная связь с `catalog_item`, если кандидат выбран из Source |
| `display_title` | Заголовок для UI; обязателен для manual / `no_provider` |
| `display_cover_url` | Обложка: URL после resolve, paste, link или upload |
| `display_summary` | Краткое описание (prefill из кандидата или manual) |
| `provider` + `external_id` | Legacy/compat поля create; заполняются из выбранного Candidate |
| `film_id` / `kinopoisk_id` | Сохраняются для существующих kinopoisk-путей create |

`CreateUserCardService` остаётся orchestrator create rated-карточки; вход `CreateUserCardInput` не меняет семантику полей — меняется только способ их заполнения на клиенте.

### Sources (не типы карточки)

**Source** — адаптер, который умеет по запросу или URL отдавать **Candidate**-ы. В доставке:

- **Kinopoisk Source** — локальный + remote search, resolve URL kinopoisk.ru.
- **RAWG Source** — search игр.
- **Manual Source** — не участвует в candidates list; активируется при пустом результате, ошибке resolve или явном «Создать вручную».

Каждый Source регистрируется в координаторах `SearchCatalogCandidatesService` и `ResolveCatalogByUrlService` (один публичный `execute` на сервис).

### Candidate (контракт UI + API)

Единый DTO для строки в picker и prefill формы:

```typescript
type CatalogCandidateKind = 'film' | 'game' | 'manual'

type CatalogCandidate = {
  candidate_id: string          // стабильный ключ строки в списке (provider:external_id или uuid для partial)
  provider: 'kinopoisk' | 'rawg' | 'no_provider'
  external_id: string | null
  kind: CatalogCandidateKind    // для иконки/группы; НЕ для автовыбора при конфликте
  kind_hint?: 'film' | 'game'   // опционально, только UI-группировка (Castlevania)
  title: string
  subtitle: string | null       // год, платформа, жанр (если есть у Source)
  cover_url: string | null
  catalog_item_id: number | null
  source: 'local' | 'remote'
  degraded?: boolean            // true если провайдер отдал урезанные данные / timeout partial
}
```

**Важно:** при нескольких кандидатах с одним названием (фильм Kinopoisk + игра RAWG) UI показывает оба; сервер **не** схлопывает их по `kind_hint`. Выбор пользователя определяет `provider`, `external_id`, `catalog_item_id` и prefill обложки.

### Разделение слоёв

- **Presentation:** `GET /api/catalog/candidates`, `POST /api/catalog/resolve-by-url`, `POST /api/cards/covers/upload`, существующие POST create.
- **Business:** orchestration Sources, merge partial results, dedup в рамках одного provider+external_id.
- **Infrastructure:** DAO/catalog clients Kinopoisk/RAWG, upload storage (тот же стек, что `UploadFeedPostImageService`).

## UI flows

### 1. Лента → action sheet (`FeedPage`)

- Заменить пару иконок на **одну кнопку «Создать»** в шапке ленты.
- По тапу — **bottom sheet** (portal overlay, паттерн как `FeedComposeSheet`) с тремя строками `Cell` из `@telegram-apps/telegram-ui`:

| Строка | Заголовок | Подзаголовок (короткий) | Действие |
|--------|-----------|-------------------------|----------|
| 1 | Карточка | Оценить фильм, сериал или игру — с обложкой и полкой | `navigate('/cards/new')` — новый UX |
| 2 | Пост | Короткая запись в ленту — мысль, ссылка, без карточки | `openCompose()` → `FeedComposeSheet` |
| 3 | Позже | Сохранить в watchlist без оценки | `navigate('/watchlist/new')` — **отдельный route**, не query-mode на `/cards/new` |

**Счётчик тапов:** «Создать» → «Карточка» = 2 тапа до smart field.

### 2. Карточка — smart entry (`CreateCardPage` redesign)

**Экран A — только поиск/выбор (fullscreen):**

- Одно поле: placeholder **«Название или ссылка»**.
- Debounced запрос `GET /api/catalog/candidates?q=…` при длине q ≥ порога (минимум как сейчас: effective 3 для kinopoisk-части, 4 для rawg — сервер нормализует).
- Если ввод распознан как URL (regex на клиенте) — вызывается `POST /api/catalog/resolve-by-url` (debounce не применяется к URL); успех → prefill + переход на форму; fail → остаёмся на entry с CTA «Заполнить вручную». Для текстового q — только `GET /api/catalog/candidates`.
- Список кандидатов: mixed, с иконкой kind (`film` / `game`), subtitle, cover thumbnail.
- Строка **«Создать вручную»** всегда внизу списка (или при пустом q) → форма с пустым manual binding.
- При tap на кандидат → **Экран B**.

**Экран B — один scroll-form (rated card):**

Секции в одном вертикальном скролле (**без stepper/progress**), порядок полей как сейчас step 3 → step 4:

1. **Тема (read-only chip)** — title, subtitle, смена через «Изменить» → back to Экран A с сохранением draft.
2. **Обложка** — см. § Cover block.
3. **Оценка** — slider 1–10, шаг 0.5.
4. **Полка / категория** — как сейчас.
5. **Компания, настроение до/после, теги, заметка** — как сейчас.
6. **Submit:** «Сохранить карточку» → `POST /api/cards` (existing) через `createMovieCard` / equivalent.

После успеха:

- `navigate('/cards/:id', { replace: true })` на страницу созданной карточки (как сейчас после rated create).
- **Вторичные действия** (не блокируют save): поделиться с подписчиками, загрузить аудио — отдельные блоки/modals **после** create, не в обязательном scroll.

**Duplicate warning:** если API вернул conflict/already exists — показать существующее предупреждение с переходом к карточке; поведение не ослабляем.

### 3. Cover block (карточка)

На scroll-form **всегда** видимый блок:

```
[ preview — poster ratio 2:3, как текущий cover preview в create flow ]
[ Загрузить ] [ Ссылка ] [ Буфер ]
```

- **Загрузить:** file picker → `POST /api/cards/covers/upload` → `display_cover_url` = returned url.
- **Ссылка:** inline input / modal для https URL → валидация на клиенте → `display_cover_url`.
- **Буфер:** paste image from clipboard (Telegram WebApp / browser API где доступно) → upload endpoint с blob.

Три кнопки **визуально равны** (не прячем upload за overflow menu). Prefill из Candidate заполняет preview; пользователь может заменить любым из трёх способов.

### 4. Пост (`FeedComposeSheet`)

- Комponent **не переписываем**; меняется только вход через sheet «Пост».
- Улучшение «clearer entry»: sheet subtitle уже объясняет intent; при открытии фокус в body; placeholder body: **«Мысль, ссылка, упоминание…»** (без смены API).
- Upload картинки поста — существующий `uploadFeedPostImage` / `POST /api/feed-posts/upload`.

### 5. Watchlist — отдельная короткая форма

- Entry **только** из пункта 3 action sheet (не из rated scroll-form, не `?mode=watchlist` на CreateCardPage).
- **Короткая форма:** smart field «название или ссылка» → pick/manual → compact поля watchlist (компания, mutual watch friends, заметка — subset текущего `watchlist` step) **без rating/mood/tags shelf**.
- Submit: `POST` create watchlist entry (existing `postCreateWatchlistEntry`) + side-effect feed post как в текущей модели watchlist-cards.
- Edit planned entry (`isEditPlannedMode`) остаётся на dedicated route/edit flow, не смешивается с rated create.

### 6. Прочие точки входа

| Точка | Поведение |
|-------|-----------|
| Deep link `/cards/new` | Новый UX (Экран A), без legacy wizard |
| Profile / FAB | **Вне scope** этой доставки — поведение не меняем |
| Inline picker в комментариях | Без изменений; не mixed candidates |

## Data model & API contracts

### GET `/api/catalog/candidates`

**Query:** `q` (string, required), `limit` (default 15), `page` (default 1).

**Behavior:**

- Параллельно опрашивает зарегистрированные Sources (Kinopoisk, RAWG).
- Merge в один `items[]`; sort: local hits first, затем remote; внутри — relevance/score per Source.
- **Partial results:** если один Source timeout/error — вернуть кандидатов от других; поле `meta.degraded_sources: string[]` в теле ответа.
- Не дедуплировать фильм vs игра с одинаковым title.

**Response:**

```json
{
  "items": [ { /* CatalogCandidate */ } ],
  "has_more": false,
  "meta": {
    "degraded_sources": ["rawg"]
  }
}
```

### POST `/api/catalog/resolve-by-url`

**Body:** `{ "url": "https://..." }`

**Behavior:**

- Определить Source по host; в этой доставке поддерживается только `kinopoisk.ru` / `www.kinopoisk.ru`; иной host → 422.
- Delegation в Source.resolve(url).
- Success → один Candidate-level payload + optional `film` embed для kinopoisk compat.

**Response (success):**

```json
{
  "catalog_item_id": 123,
  "provider": "kinopoisk",
  "external_id": "301",
  "kind": "film",
  "title": "...",
  "cover_url": "...",
  "summary": "...",
  "film": { /* existing Film shape for kinopoisk */ }
}
```

**Errors:** 422/404 → клиент показывает manual path; не блокирует форму навсегда.

*Замена клиентского паттерна:* вместо `inferCatalogProviderFromUrl` + `POST /api/catalog/resolve` с `{ provider, url }` — один URL-first endpoint. Legacy `POST /api/catalog/resolve` может остаться для compat, но новый UI использует только `resolve-by-url`.

### POST `/api/cards/covers/upload`

**Request:** `multipart/form-data`, field `file` — как feed post upload.

**Response:**

```json
{ "url": "/api/cards/media/…" }
```

**Constraints:** те же лимиты размера/MIME, что `FEED_POST_IMAGE_MAX_BYTES` и allowed content types; storage adapter может общий RustFS bucket с другим prefix.

### POST `/api/cards` (existing)

Без breaking changes. Client после pick/manual отправляет:

```json
{
  "rating": 8.5,
  "company": "alone",
  "mood_before": "relax",
  "mood_after": "enjoyed",
  "custom_tags": [],
  "watch_note": "",
  "catalog_item_id": 123,
  "provider": "kinopoisk",
  "external_id": "301",
  "display_title": null,
  "display_cover_url": "https://… or uploaded path",
  "display_summary": null,
  "category_id": null
}
```

Manual path:

```json
{
  "rating": 7,
  "…": "…",
  "catalog_item_id": null,
  "provider": "no_provider",
  "display_title": "Мой кастомный тайтл",
  "display_cover_url": "/api/cards/media/…",
  "display_summary": "…"
}
```

Validation rules из `CreateUserCardInput` / schemas **без изменений**.

### Watchlist & feed post APIs

- `postCreateWatchlistEntry`, `createFeedPost` — **без изменения контрактов** в этой доставке.
- Watchlist form заполняет те же поля, что сегодняшний watchlist branch, но через отдельную страницу.

## Error handling

| Ситуация | UX | API |
|----------|-----|-----|
| Source timeout | Показать partial list + subtle hint «не все источники ответили» | 200 + `meta.degraded_sources` |
| Оба Source fail | Пустой list + «Создать вручную» | 200 + `items: []` (не 503) |
| Resolve URL fail | Toast «Не удалось разобрать ссылку» + manual | 404/422 |
| Duplicate card | Existing warning + link to card | 409 / domain error mapping unchanged |
| Upload fail | Inline error под preview | 400/413/503 как feed upload |
| Auth | Redirect/login | 401 |
| Offline / network | Retry on candidates; **без** persist draft в localStorage в v1 |

**Castlevania:** не ошибка — два кандидата в списке; пользователь обязан выбрать.

## Migration от текущего 4-step wizard

Текущий `CreateCardPage` (`WizardStep` 1→2→3→4 + branch `watchlist`):

| Legacy step | Title | Новое место |
|-------------|-------|-------------|
| 1 «Что добавляем» | Выбор film/game/custom | **Удалить** → smart field |
| 2 «Проверьте тему» | Confirm binding | **Удалить** → tap candidate или manual |
| watchlist branch | «Детали для Позже» | **Перенести** на `/watchlist/new` (sheet item 3) |
| 3 «Оценка и полка» | Rating + category | **Scroll-form секции** |
| 4 «Детали и отправка» | Moods, tags, note, share | **Scroll-form секции**; share/audio **after create** |

**Frontend:**

- Переписать `CreateCardPage.tsx`: убрать `wizardProgressPercent`, step state machine, `branchWatchlist`.
- Новые hooks: `useCatalogCandidates`, `useResolveCatalogUrl`, `useCardCoverUpload`.
- `catalogApi.ts`: добавить `searchCatalogCandidates`, `resolveCatalogByUrl`; старые `searchCatalog(provider)` — deprecate для create flow, можно оставить для других экранов.
- `FeedPage.tsx`: single «Создать» + action sheet.
- Новая страница `CreateWatchlistPage` на route `/watchlist/new` (отдельно от `/cards/new`).

**Backend:**

- Новые routes + services для candidates и resolve-by-url.
- `UploadUserCardCoverService` mirror `UploadFeedPostImageService`.
- Без миграций БД для core model — поля уже есть.

**Rollout:** big-bang замена wizard на новый UX при merge; feature flag не требуется по spec.

## Testing & verification

### Backend (pytest inside Docker)

- `GET /api/catalog/candidates`: happy path merge kinopoisk+rawg; empty q; pagination; partial when one Source mocked timeout; no over-dedup film+game same title.
- `POST /api/catalog/resolve-by-url`: kinopoisk URL happy; unknown host → 422; not found → 404.
- `POST /api/cards/covers/upload`: success; oversize 413; bad MIME 400.
- Regression: `POST /api/cards` with `catalog_item_id` path and `no_provider` manual path unchanged.
- Watchlist create from new page still creates entry + feed post.

Commands: `make backend-test`, targeted `make backend-test-one target=…`.

### Frontend

- `cd frontend && npm run lint && npm run build` — zero errors in touched files.
- Manual QA checklist:
  - Feed → Создать → Карточка → 2 taps to field.
  - Paste kinopoisk URL → resolve → scroll form with cover preview.
  - Castlevania → two rows → pick game → correct provider on save.
  - Cover: upload, link, buffer each update preview.
  - Duplicate card warning still appears.
  - Feed → Пост → FeedComposeSheet opens.
  - Feed → Позже → short form, no rating slider.

## Future: YouTube as another Source

YouTube не входит в доставку. Расширение:

1. Реализовать `YouTubeSource` с `search(q)` и `resolve(url)` → `CatalogCandidate` (`kind: 'film'` или отдельный `kind: 'video'` — решение при подключении; контракт Candidate расширяем).
2. Зарегистрировать в coordinator — **без изменений** `UserCard` model и `POST /api/cards` shape.
3. UI автоматически покажет YouTube строки в mixed list и resolve-by-url для youtube.com / youtu.be.

Клиент не должен hardcode список провайдеров для create flow — только отображать `provider`/`kind` из Candidate.

## Open implementation notes

Конкретные ограничения для имплементации (не открытые вопросы):

- **Route watchlist create:** `/watchlist/new` (`CreateWatchlistPage` в `routes.tsx`); query `?mode=watchlist` на `/cards/new` **не использовать**.
- **`kind_hint`:** поле только в API response для UI; **не отправляется** на create и **не влияет** на server-side disambiguation.
- **Candidate `candidate_id`:** строка `"{provider}:{external_id}"` для catalog hits; для degraded partial без external_id — uuid v4 в ответе только на этот request.
- **Cover upload URL prefix:** `/api/cards/media/{key}` — symmetric to feed posts media route.
- **Scroll-form state:** при «Изменить тему» возврат на Экран A сохраняет rating/tags draft in memory (session); не persist localStorage в v1.
- **Action sheet copy (RU):** подзаголовки из таблицы § UI flows — финальный текст, не lorem.
- **ComposeFeedPostProvider:** остаётся глобальным; sheet «Пост» вызывает `openCompose()` без payload изменений.
- **Не переименовывать** `createMovieCard`, `MovieCard` types в frontend в этой задаче — только UX/API additions.
