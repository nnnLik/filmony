# Telegram Mini App — UI и UX профиля

Краткий архив решений и файлов (дополнение к `profile-and-public-profiles`).

## Тёмная тема и палитра

- Принудительно `appearance="dark"` в `AppRoot`, класс `filmony-theme` с переопределением `--tgui--*` и `--tg-theme-*` под палитру «midnight bioluminescence» (мятный акцент, тёплый янтарь для вторичных состояний).
- Фон страницы: радиальный градиент + `--filmony-ink` в `frontend/src/index.css`.

## Нижняя навигация

- Плавающая «док-панель»: скругление, blur, обводка, активная вкладка — пилюля (мята для ленты, янтарь для профиля).
- Файл: `frontend/src/components/navigation/BottomNav.tsx`, отступ контента в `frontend/src/layout/AppShell.tsx`.

## Кеш и уменьшение «мигания» загрузки

- **Сессия TMA:** после успешного `POST /api/auth/telegram` в `sessionStorage` ставится флаг; при следующем открытии вкладки старт с `auth.kind === 'ready'` (оптимистично), повторная проверка в фоне. При ошибке входа флаг и кеш профиля сбрасываются.
- **Профиль:** снимок `{ profile, cards, storedAt }` в `sessionStorage` (TTL 12 мин), мгновенный показ на `/profile` до ответа API.
- Файлы: `frontend/src/lib/filmonySession.ts`, `frontend/src/lib/myProfileBundleCache.ts`, правки `frontend/src/auth/AuthProvider.tsx`, `frontend/src/pages/ProfilePage.tsx`.

## Редактирование профиля

- Форма вынесена на маршрут `/profile/edit`; шестерёнка в шапке профиля ведёт туда.
- Файлы: `frontend/src/pages/ProfileEditPage.tsx`, `frontend/src/routes.tsx`, `frontend/src/pages/ProfilePage.tsx`.

## Публичная ссылка

- На профиле — блок «Публичная ссылка»; по нажатию копируется полный URL (`origin` + `/u/{slug}`), тост через `Snackbar`.
- Утилита: `frontend/src/lib/publicProfileUrl.ts`.

## Текстовые блоки с фоном

- Класс `.filmony-text-panel` в `index.css`: скругление, фон, бордер; применён к подсказкам, пустым состояниям, ошибкам, био, деталям статистики и т.д. на ленте, профиле, публичном профиле, хедере профиля.

## Прочее

- Публичный профиль: при смене `identifier` очищается старый профиль только при реальной смене маршрута (`useRef`), без лишнего сброса при повторном заходе на того же пользователя.
- Файл: `frontend/src/pages/PublicProfilePage.tsx`.

## Проверка

- Рекомендуется: `cd frontend && npm run build && npm run lint`.
