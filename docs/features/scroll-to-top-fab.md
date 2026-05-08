# Кнопка «Наверх» при прокрутке

## Поведение

- После прокрутки вниз примерно **на 240px** справа внизу появляется круглая кнопка со стрелкой вверх (`IconButton` + `ChevronUp`).
- По нажатию выполняется **`scrollTo({ top: 0, behavior: 'smooth' })`**; при `prefers-reduced-motion: reduce` — мгновенный скролл.
- На маршрутах с **нижней навигацией** (`/`, `/profile…`, `/cards/new`) отступ снизу совпадает с запасом под `BottomNav`; на остальных — ближе к краю экрана.

## Файлы

- [`frontend/src/components/navigation/ScrollToTopFab.tsx`](../../frontend/src/components/navigation/ScrollToTopFab.tsx)
- Подключение: [`frontend/src/App.tsx`](../../frontend/src/App.tsx)

## Ручная проверка

Откройте длинную страницу (лента с карточками), прокрутите вниз — кнопка должна плавно появиться; нажатие ведёт плавно к началу страницы.
