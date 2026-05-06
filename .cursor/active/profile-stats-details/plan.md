# Implementation Plan — profile-stats-details

## Feature
- Slug: `profile-stats-details`
- Source spec: `.cursor/features/profile-stats-details/feature.md`

## Goal
Реализовать полноценный блок статистики карточек фильмов и отобразить его на страницах своего и публичного профиля.

## Step-by-Step Plan
1. Добавить backend сервис агрегирования статистики карточек пользователя.
2. Расширить API-схемы профиля и добавить `GET /api/users/{user_id}/stats`.
3. Добавить backend тесты на auth/not-found/happy-path агрегатов и top/worst.
4. Добавить frontend типы + API клиент для нового endpoint.
5. Реализовать общий UI-компонент `ProfileStatsPanel`.
6. Подключить `ProfileStatsPanel` в `ProfilePage` и `PublicProfilePage` (вкладка «Статистика»).
7. Обновить docs и action-log.

## Verification Plan
- Backend: `make backend-test-one target=src/tests/api/test_profile_routes.py::test_user_stats_aggregates`
- Frontend: `cd frontend && npm run lint`
