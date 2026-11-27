# Custom profile avatar

On your profile and in profile settings, the avatar can be replaced with a JPEG, PNG, WebP, or GIF up to 5 MB. A pencil appears on hover, and on touch it stays visible. Clicking the avatar opens the file picker. While a custom photo is set, it can be removed; the Telegram photo comes back.

The file is stored in RustFS at `user_media/avatars/{user_id}`. `User.photo_url` points at `GET /api/users/avatar-media/...`. Replacing deletes that object and uploads the new file. Login does not overwrite `photo_url` until the custom photo is removed.

Removal restores `https://t.me/i/userpic/320/{username}.jpg` when a username exists. Without a username the profile stores `GET /api/users/{id}/telegram-avatar`, which streams the current Telegram photo without putting the bot token in the URL. The next login writes the usual Telegram CDN URL again.
