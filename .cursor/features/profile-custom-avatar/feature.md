# Custom profile avatar

## Metadata
- Feature slug: `profile-custom-avatar`
- Status: done
- Created at: 2026-11-28

## Goal
Let a user set their own profile photo. Until they do, the avatar stays the Telegram photo. The displayed photo is never cleared to an empty string.

## Acceptance criteria
- [x] Own profile and profile edit: hover (and always on touch) shows a pencil; click opens a file picker.
- [x] JPEG, PNG, WebP, GIF up to 5 MB. Empty and non-image files are rejected.
- [x] The file is stored in RustFS at `user_media/avatars/{user_id}`. `photo_url` points at the public media path. No new database columns.
- [x] Replacing deletes the previous object, then uploads the new one. If the new upload fails, `photo_url` returns to the Telegram photo.
- [x] Removing the custom photo deletes the object and restores the Telegram photo (`t.me/i/userpic` when a username exists, otherwise a bot-token-free proxy).
- [x] Telegram login does not overwrite `photo_url` while a custom avatar is set.
- [x] Relative media URLs resolve through `VITE_API_ORIGIN` everywhere a user avatar is rendered.
