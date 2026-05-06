# Implementation Plan — frontend-subscriptions-ui

## Feature
- Slug: `frontend-subscriptions-ui`
- Source spec: `.cursor/features/frontend-subscriptions-ui/feature.md`

## Goal
Добавить полноценный UX подписок во фронтенде с отдельной страницей, переходами из счётчиков профиля и действиями follow/unfollow.

## Steps
1. Расширить API-типы и клиент подписок в `frontend/src/api/profileTypes.ts` и `frontend/src/api/profileApi.ts`.
2. Создать `frontend/src/pages/SubscriptionsPage.tsx` с логикой списка подписчиков/подписок.
3. Подключить роуты `/profile/subscriptions` и `/u/:identifier/subscriptions`.
4. Обновить `ProfilePage` и `PublicProfilePage`: счётчики и переходы; на публичном профиле добавить кнопку follow/unfollow.
5. Проверить изменённые файлы через линтер/диагностики и зафиксировать артефакты.

## Verification
- IDE diagnostics (`ReadLints`) по изменённым фронтовым файлам.
- Локально рекомендуется: `npm run lint && npm run build` в `frontend/`.
