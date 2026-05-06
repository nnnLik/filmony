# 2026-05-06T04:40:00Z

- Feature slug: `profile-address-lockdown`
- Action type: refactor | code
- Summary: Убрана возможность менять публичный адрес; PATCH `/api/me/profile` больше не принимает `profile_slug`; удалён backend endpoint профиля по slug; фронт переведён на `/u/:userId`; поле редактирования публичного адреса убрано.
- Files:
  - `backend/src/api/profile/{schemas.py,me_routes.py,users_routes.py}`
  - `backend/src/services/profile/update_my_profile.py`
  - `backend/src/tests/api/test_profile_routes.py`
  - `frontend/src/lib/publicProfileUrl.ts`
  - `frontend/src/api/profileApi.ts`
  - `frontend/src/routes.tsx`
  - `frontend/src/pages/{PublicProfilePage.tsx,SubscriptionsPage.tsx,ProfileEditPage.tsx}`
- Verification: `ReadLints` по изменённым backend/frontend файлам: ошибок нет.
- Links:
  - `backend/src/tests/api/test_profile_routes.py`
  - `frontend/src/pages/ProfileEditPage.tsx`
