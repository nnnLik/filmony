# Plan — profile-custom-avatar

Status: done

1. Keep a single `User.photo_url`. Custom file key is `user_media/avatars/{user_id}`.
2. `POST /api/me/avatar` validates type and signature, deletes the previous object when replacing, then puts the new bytes.
3. `DELETE /api/me/avatar` deletes the object and writes the Telegram URL back.
4. Login skips `photo_url` when it is already a custom media path.
5. Public `GET /api/users/avatar-media/...` and `GET /api/users/{id}/telegram-avatar`.
6. Own profile and edit screen: pencil, file input, remove control when the photo is custom.
7. `userPhotoSrc` on every user avatar render.
