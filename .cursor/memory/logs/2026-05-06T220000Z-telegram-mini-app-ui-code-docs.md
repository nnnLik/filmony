# 2026-05-06T22:00:00Z

- Feature slug: `telegram-mini-app-ui`
- Action type: code | docs
- Summary: Тёмная палитра Filmony и переопределение tgui-токенов; плавающий нижний навбар; кеш sessionStorage для auth и бандла "мой профиль + карточки"; экран `/profile/edit`; копирование публичной ссылки + Snackbar.
- Files:
  - `frontend/src/index.css`
  - `frontend/src/App.tsx`
  - `frontend/src/layout/AppShell.tsx`
  - `frontend/src/components/navigation/BottomNav.tsx`
  - `frontend/src/auth/AuthProvider.tsx`
  - `frontend/src/lib/{filmonySession.ts,myProfileBundleCache.ts,publicProfileUrl.ts}`
  - `frontend/src/pages/{ProfilePage.tsx,ProfileEditPage.tsx,FeedPage.tsx,PublicProfilePage.tsx}`
  - `frontend/src/components/profile/ProfileHeader.tsx`
  - `frontend/src/routes.tsx`
  - `.cursor/memory/features/telegram-mini-app-ui.md`
- Verification: рекомендуется `cd frontend && npm run build && npm run lint` (в сессии не зафиксировано).
- Links:
  - `.cursor/memory/features/telegram-mini-app-ui.md`
