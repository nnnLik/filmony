# Progress — frontend-subscriptions-ui

## Status
- **done**

## Log
- Добавлены типы и API-вызовы подписок в `profileTypes.ts` и `profileApi.ts`.
- Создана страница `SubscriptionsPage`:
  - поддержка своего и чужого профиля,
  - переключатель `Подписки / Подписчики`,
  - follow/unfollow actions,
  - блок шаринга ссылки для своего профиля.
- Добавлены роуты:
  - `/profile/subscriptions`
  - `/u/:identifier/subscriptions`
- На `ProfilePage`:
  - добавлены 3 KPI-счётчика,
  - клики по первым двум ведут на страницу подписок с query-параметром вкладки.
- На `PublicProfilePage`:
  - добавлены 3 KPI-счётчика,
  - клики по первым двум ведут на публичную страницу подписок,
  - добавлена кнопка `Подписаться/Отписаться`.
- Проверка `ReadLints` по изменённым файлам: ошибок нет.
- Прямой запуск shell-команд (`npm run lint`, `npm run build`) в этой сессии не выполнен, так как shell-вызовы были отклонены интерфейсом (`User chose to skip`).
