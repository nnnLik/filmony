# Локальные «Недавно открывали» и копирование ссылки на карточку

## Цель

- Дать пользователю **скопировать deep link** на Mini App для конкретной карточки (как в Telegram-уведомлениях: `https://t.me/<бот>/app?startapp=c<id>`).
- Показать на **ленте** компактную полоску **последних 3–5 карточек**, которые пользователь открывал на деталке, **без сервера** — только `localStorage` по id текущего пользователя.

## Конфигурация фронта

| Переменная | Назначение |
|------------|------------|
| `VITE_TELEGRAM_BOT_USERNAME` | Имя бота без `@`, то же по смыслу, что `TELEGRAM_BOT_USERNAME` на бэкенде. Без него кнопки копирования ссылки **скрыты**. |

Шаблоны: [`vars/.env.example`](../../vars/.env.example), [`vars/.env.development`](../../vars/.env.development).

Формат ссылки совпадает с бэкендом: [`backend/src/services/telegram/mini_app_link.py`](../../backend/src/services/telegram/mini_app_link.py). Открытие из Telegram обрабатывается в [`frontend/src/navigation/TelegramMiniAppStartParamRedirect.tsx`](../../frontend/src/navigation/TelegramMiniAppStartParamRedirect.tsx).

## Поведение

### Копирование ссылки

- **Деталка карточки** ([`MovieCardDetailPage.tsx`](../../frontend/src/pages/MovieCardDetailPage.tsx)): иконка «ссылка» (`Link2`) рядом с «Поделиться» / «Взять за основу» — копирует URL в буфер.
- **Экран «Поделиться»** ([`ShareMovieCardPage.tsx`](../../frontend/src/pages/ShareMovieCardPage.tsx)): кнопка «Скопировать ссылку» в [`ShareFollowersPicker`](../../frontend/src/components/share/ShareFollowersPicker.tsx) под превью фильма.

Утилиты: [`frontend/src/lib/miniAppCardDeepLink.ts`](../../frontend/src/lib/miniAppCardDeepLink.ts), [`frontend/src/lib/copyTextToClipboard.ts`](../../frontend/src/lib/copyTextToClipboard.ts).

### Недавно открывали

- При успешной загрузке карточки и известном id зрителя вызывается `recordRecentCardView` ([`recentCardViews.ts`](../../frontend/src/lib/recentCardViews.ts)).
- Ключ в `localStorage`: `filmony.recent_cards.<user_uuid>`, не более **5** записей, дубликаты по `id` поднимаются в начало.
- **Лента** ([`FeedPage.tsx`](../../frontend/src/pages/FeedPage.tsx)): блок [`RecentCardsStrip`](../../frontend/src/components/feed/RecentCardsStrip.tsx) под шапкой; обновление при `visibilitychange`, при кастомном событии `filmony-recent-cards-changed` (после записи на деталке).

Список на ленте читается из кеша профиля (`readMyProfileBundleCache`) для получения `user id`; если кеша ещё нет, полоска пуста до появления id в кеше (например после визита профиля).

## Проверка (локально)

1. В `vars/.env.development` задайте `VITE_TELEGRAM_BOT_USERNAME` так же, как бота в BotFather (как `TELEGRAM_BOT_USERNAME`). Перезапустите `npm run dev`, чтобы Vite подхватил переменную.
2. Поднимите стек (`make start` и при nginx-разработке — как в [README](../../README.md)), откройте приложение через **http://127.0.0.1:8888** (или ваш URL).
3. **Копирование с деталки:** откройте любую карточку → нажмите иконку ссылки рядом с «Поделиться»/«Взять за основу» → вставьте из буфера в поле — должна быть ссылка вида `https://t.me/.../app?startapp=c<число>`.
4. **Копирование с шаринга:** своя карточка → «Поделиться» → под превью нажмите «Скопировать ссылку» → та же проверка буфера.
5. **Недавно открывали:** откройте 1–2 карточки с деталки, вернитесь на **Ленту** — под заголовком «Лента» появляется блок «Недавно открывали» с постерами; переход по миниатюре ведёт на `/cards/:id`.
6. **Без бота:** временно уберите или очистите `VITE_TELEGRAM_BOT_USERNAME`, пересоберите dev — иконка ссылки и кнопка «Скопировать ссылку» не должны отображаться (страница без ошибок).

## Файлы

| Область | Путь |
|---------|------|
| Deep link | `frontend/src/lib/miniAppCardDeepLink.ts` |
| Буфер обмена | `frontend/src/lib/copyTextToClipboard.ts` |
| История просмотров | `frontend/src/lib/recentCardViews.ts` |
| Полоска на ленте | `frontend/src/components/feed/RecentCardsStrip.tsx` |
| Лента | `frontend/src/pages/FeedPage.tsx` |
| Деталка | `frontend/src/pages/MovieCardDetailPage.tsx` |
| Шаринг | `frontend/src/components/share/ShareFollowersPicker.tsx`, `frontend/src/pages/ShareMovieCardPage.tsx` |
| Типы env | `frontend/src/vite-env.d.ts` |

## Ограничения

- Нет синхронизации между устройствами; очистка данных браузера сбрасывает «Недавно откры-vали».
- Ссылка пригодна для открытия в **Telegram**; в обычном браузере по ней откроется диалог с ботом.
