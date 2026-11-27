# Result — profile-custom-avatar

Status: done

## Implemented
Users can upload a profile photo from their own profile and the edit screen. The file lives in RustFS. `photo_url` switches to that media URL and switches back to the Telegram photo when the custom file is removed. Login does not wipe a custom photo. No new columns.

## Changed files
- `backend/src/utils/avatar_photo_url.py`
- `backend/src/services/profile/set_my_avatar.py`
- `backend/src/services/profile/clear_my_avatar.py`
- `backend/src/services/profile/avatar_object_storage.py`
- `backend/src/services/profile/resolve_telegram_avatar_url.py`
- `backend/src/services/profile/get_avatar_media.py`
- `backend/src/services/profile/get_telegram_avatar_bytes.py`
- `backend/src/services/auth/upsert_telegram_user.py`
- `backend/src/integrations/telegram/bot_api_client.py`
- `backend/src/api/profile/me_routes.py`
- `backend/src/api/profile/users_routes.py`
- `frontend/src/components/profile/OwnProfileAvatar.tsx`
- `frontend/src/lib/userPhotoSrc.ts`
- `frontend/src/components/profile/ProfileHeader.tsx`
- `frontend/src/pages/ProfilePage.tsx`
- `frontend/src/pages/ProfileEditPage.tsx`

## Verification
- Docker pytest, 13 passed:
  - `src/tests/unit/services/auth/test_upsert_telegram_user_avatar.py`
  - `src/tests/unit/services/profile/test_set_my_avatar.py`
  - `src/tests/unit/services/profile/test_clear_my_avatar.py`
  - `src/tests/integration/api/test_profile_avatar_routes.py`
- `ruff check` on the touched backend files.
- `cd frontend && npm run lint && npm run build` (lint exit 0; one pre-existing warning in `WatchPartyChatList.tsx`).

The profile screen was not clicked in a browser: the Filmony app container was stopped, and upload needs a Telegram session.

## Limitations
- No crop step.
- Without a Telegram username, removal stores `/api/users/{id}/telegram-avatar` until the next login writes the CDN `photo_url` from initData.
- If Telegram has no photo, `photo_url` becomes null and the UI shows initials.
