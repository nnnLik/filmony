# Feature: frontend-subscriptions-ui

## Назначение
Реализует UX подписок во фронтенде по макетам: счётчики в профиле, переходы в экран подписок, кнопки follow/unfollow, шаринг ссылки на свой профиль.

## Что добавлено

### Профили
- На экране своего профиля (`/profile`) под именем отображаются:
  - количество подписчиков,
  - количество подписок,
  - количество фильмов.
- На экране чужого профиля (`/u/:identifier`) отображается такой же блок счётчиков.
- Клик по `подписчики` и `подписки` открывает экран подписок с нужной вкладкой.
- На чужом профиле добавлена кнопка `Подписаться/Отписаться`.

### Экран подписок
- Добавлена страница:
  - `/profile/subscriptions`
  - `/u/:identifier/subscriptions`
- На странице:
  - переключатель `Подписки / Подписчики`,
  - список пользователей,
  - действие `Подписаться/Отписаться` у каждого пользователя (кроме самого себя),
  - для своего профиля — блок с публичной ссылкой и кнопкой копирования.

## API интеграция
- `POST /api/users/{user_id}/subscriptions`
- `DELETE /api/users/{user_id}/subscriptions`
- `GET /api/users/{user_id}/subscriptions?type=followers|following|both`
- Поля профиля: `followers_count`, `following_count`.

## Файлы
- `frontend/src/api/profileTypes.ts`
- `frontend/src/api/profileApi.ts`
- `frontend/src/pages/SubscriptionsPage.tsx`
- `frontend/src/pages/ProfilePage.tsx`
- `frontend/src/pages/PublicProfilePage.tsx`
- `frontend/src/routes.tsx`
