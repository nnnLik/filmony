# Action log — profile custom avatar closeout

- **Timestamp:** 2026-11-27T214500Z
- **Feature slug:** profile-custom-avatar
- **Action type:** closeout
- **Summary:** Users can upload or remove a profile photo stored in RustFS. `photo_url` stays the only column; Telegram login does not overwrite a custom avatar.

## Files

- `backend/src/services/profile/set_my_avatar.py`
- `backend/src/services/profile/clear_my_avatar.py`
- `backend/src/services/auth/upsert_telegram_user.py`
- `backend/src/api/profile/me_routes.py`
- `frontend/src/components/profile/OwnProfileAvatar.tsx`
- `docs/features/profile-custom-avatar.md`

## Verification

- Docker pytest: unit upsert/set/clear plus `src/tests/integration/api/test_profile_avatar_routes.py` (13 passed)
- `cd frontend && npm run lint && npm run build`
